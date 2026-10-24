"""Grounded answers: rewrite follow-ups, split multi-part questions, gather passages,
stream Qwen's answer, then check its citations.

Speed (measured 2026-10-23 on the 27B): the helper steps run with thinking off
(about 2-4 s each, and only when needed); the answer keeps low thinking, which got
"which class" questions right where thinking off did not.
"""
import json
import re
from typing import AsyncIterator, Optional

import httpx

from handouts import knowledge, store
from handouts.retrieve import _passages, daniel_glossary, fuse, search

MAX_SOURCES = 8  # simple questions; multi-part ones get MAX_SOURCES_MULTIPART
MAX_SOURCES_MULTIPART = 10
SOURCE_WORD_BUDGET = 6500  # about 9,000 tokens, leaving room for the answer
MIN_CITED_SHARE = 0.5
HISTORY_TURNS = 3
MAX_EVIDENCE = 4  # extra passages pulled in because a knowledge-map fact points at them
MAP_LINES = 16
# Facts most useful for answering come first.
FACT_ORDER = ["introduced_in", "done_in_class", "releases", "is_source_of", "requires", "located_in",
              "is_part_of", "related_to"]
FACT_WORDS = {"introduced_in": "is introduced in", "done_in_class": "is done in", "releases": "releases",
              "is_source_of": "is a source of", "is_part_of": "is part of", "requires": "requires",
              "located_in": "is located in", "related_to": "is related to"}

ANSWER_PROMPT = """You answer questions about VortexHealing class handouts using only the numbered sources given.
Cite sources as [n] after each claim. When you combine sources into a conclusion that none of them states,
start that sentence with "Inference:". If the sources do not answer the question, say "The handouts don't cover
this" and name the closest sources. Never add knowledge from outside the sources. Write plain prose, with short
headings when the answer has parts (what it is, where it comes from, which tools, which class).
Be concise: about 250 words unless the question asks for a list, a protocol or a comparison.
Each source is labelled with its handout's title. A handout titled "<Class> Review" is the review for that class,
so "in this class" inside it means that class.
Teacher notes, when given, come from the teacher and override the handouts where they disagree.
A "Knowledge map" list may follow the sources: facts already taken from those sources, each ending with its
source number. Use it to connect and compare classes (for example how something is done in one class and
another), and cite the source numbers it gives."""

REWRITE_PROMPT = """Rewrite the follow-up question as one complete question that makes sense on its own,
using the conversation for what "it", "that", "they" and similar words refer to. Reply with the question only."""

SPLIT_PROMPT = """Split the question into at most 3 short search queries, one per part of the question.
Reply with a JSON array of strings only, for example ["source of fear", "tools that release fear"]."""


class QwenUnavailable(Exception):
    pass


def _model_and_url() -> tuple[str, str]:
    from app.core.config import settings

    return settings.QWEN_MODEL, f"{settings.LM_STUDIO_URL}/chat/completions"


async def complete(messages: list[dict], effort: str, max_tokens: int) -> str:
    model, url = _model_and_url()
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(url, json={"model": model, "messages": messages, "temperature": 0,
                                             "max_tokens": max_tokens, "reasoning_effort": effort})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise QwenUnavailable(type(e).__name__) from e


async def stream(messages: list[dict], effort: str, max_tokens: int) -> AsyncIterator[tuple[str, str]]:
    """Yields ("thinking", chunk) and ("text", chunk) as LM Studio produces them."""
    model, url = _model_and_url()
    body = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens,
            "reasoning_effort": effort, "stream": True}
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", url, json=body) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    for choice in json.loads(line[6:]).get("choices", []):
                        delta = choice.get("delta", {})
                        if thinking := delta.get("reasoning_content") or delta.get("reasoning"):
                            yield "thinking", thinking
                        if text := delta.get("content"):
                            yield "text", text
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise QwenUnavailable(type(e).__name__) from e


async def rewrite(question: str, history: list[dict]) -> str:
    if not history:
        return question
    convo = "\n".join(f"Q: {h.get('q', '')}\nA: {h.get('answer', '')[:600]}" for h in history[-HISTORY_TURNS:])
    out = await complete([{"role": "system", "content": REWRITE_PROMPT},
                          {"role": "user", "content": f"Conversation:\n{convo}\n\nFollow-up: {question}"}], "none", 120)
    first = next((ln.strip().strip('"') for ln in out.splitlines() if ln.strip()), "")
    return first or question


def is_multipart(question: str) -> bool:
    return len(question.split()) >= 8 and (bool(re.search(r"\band\b|[,;]", question)) or question.count("?") > 1)


async def split(question: str) -> list[str]:
    if not is_multipart(question):
        return []
    out = await complete([{"role": "system", "content": SPLIT_PROMPT},
                          {"role": "user", "content": question}], "none", 200)
    match = re.search(r"\[.*\]", out, re.S)
    try:
        parts = json.loads(match.group(0)) if match else []
    except ValueError:
        return []
    return [p.strip() for p in parts if isinstance(p, str) and p.strip()][:3]


def gather(question: str, searches: list[str], conn=None, limit: int = MAX_SOURCES) -> list[dict]:
    """Passages for the question and each sub-query, fused, at most 3 per handout, within the word budget."""
    by_id: dict[int, dict] = {}
    rankings = []
    for q in [question, *searches]:
        hits = search(q, limit=20, conn=conn)
        by_id.update({h["chunk_id"]: h for h in hits})
        rankings.append([h["chunk_id"] for h in hits])
    fused = fuse(rankings)
    chosen, per_doc, words = [], {}, 0
    for cid in sorted(fused, key=fused.get, reverse=True):
        p = by_id[cid]
        size = len(p["text"].split())
        if per_doc.get(p["document_id"], 0) >= 3 or words + size > SOURCE_WORD_BUDGET:
            continue
        per_doc[p["document_id"]] = per_doc.get(p["document_id"], 0) + 1
        words += size
        chosen.append(p)
        if len(chosen) >= limit:
            break
    return chosen


def add_evidence(conn, passages: list[dict], cards: list[dict]) -> tuple[list[dict], list[str]]:
    """Adds the passages behind the cards' key facts and returns the knowledge-map lines that cite them."""
    passages = list(passages)
    by_section = {}
    for i, p in enumerate(passages, 1):
        sec = conn.execute("select section_id from chunks where id = ?", (p["chunk_id"],)).fetchone()
        if sec:
            by_section.setdefault(sec[0], i)
    lines, added = [], 0
    for c in cards:
        for f in sorted(c["facts"], key=lambda f: FACT_ORDER.index(f["predicate"])):
            section_id = f["source"]["section_id"]
            if section_id not in by_section and added < MAX_EVIDENCE:
                first = conn.execute("select id from chunks where section_id = ? order by ord limit 1", (section_id,)).fetchone()
                found = _passages(conn, [first[0]], {first[0]: 0.0}, 1) if first else []
                if found:
                    passages.append(found[0])
                    by_section[section_id] = len(passages)
                    added += 1
            if section_id not in by_section:
                continue
            detail = f" ({f['detail']})" if f["detail"] else ""
            line = f"- {c['name']} {FACT_WORDS[f['predicate']]} {f['object']}{detail} [{by_section[section_id]}]"
            if line not in lines:
                lines.append(line)
            if len(lines) >= MAP_LINES:
                return passages, lines
    return passages, lines


def sources_text(passages: list[dict]) -> str:
    def label(p):
        if p.get("source_kind") == "note":
            return f"Teacher note ({p.get('doc_date') or p['title']})"
        version = f", version {p['version']}" if p.get("version") else ""
        return f"{p['title']}{version} — {p['heading_path'] or 'opening section'}"
    return "\n\n".join(f"[{i}] {label(p)}\n{p['text']}" for i, p in enumerate(passages, 1))


def system_prompt() -> str:
    gloss = daniel_glossary()
    if not gloss:
        return ANSWER_PROMPT
    terms = "; ".join(f"{abbr} = {' / '.join(v)}" for abbr, v in gloss.items() if "?" not in " ".join(v))
    return f"{ANSWER_PROMPT}\nAbbreviations used in the handouts: {terms}."


def check_citations(answer: str, n_sources: int) -> tuple[str, float]:
    """Removes citations to sources that do not exist; returns the cleaned answer and the share
    of substantial paragraphs or bullets that cite at least one source."""
    cleaned = re.sub(r"\[(\d+)\]", lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "", answer)
    blocks = [b for b in cleaned.splitlines()
              if len(b.split()) >= 8 and not b.lstrip().startswith("#") and "don't cover" not in b]
    if not blocks:
        return cleaned.strip(), 1.0
    return cleaned.strip(), sum(bool(re.search(r"\[\d+\]", b)) for b in blocks) / len(blocks)


async def ask(question: str, history: Optional[list[dict]] = None, conn=None) -> AsyncIterator[dict]:
    """Events for the page: sources, thinking, text chunks, then done (or error)."""
    try:
        standalone = await rewrite(question, history or [])
        searches = await split(standalone)
    except QwenUnavailable:
        standalone, searches = question, []
    passages = gather(standalone, searches, conn=conn, limit=MAX_SOURCES_MULTIPART if searches else MAX_SOURCES)
    kconn = conn or store.connect(_db_path())
    cards = [c for c in (knowledge.card(kconn, i) for i in knowledge.find_entities(kconn, standalone)) if c]
    passages, map_lines = add_evidence(kconn, passages, cards)
    yield {"type": "sources", "question": standalone, "rewritten": standalone != question,
           "searches": searches, "passages": passages, "cards": [trim(c) for c in cards]}
    if not passages:
        yield {"type": "done", "answer": "The handouts don't cover this: nothing matched the question.",
               "cited_share": 1.0, "fallback": False}
        return
    messages = [{"role": "system", "content": system_prompt()},
                {"role": "user", "content": f"Sources:\n\n{sources_text(passages)}\n\n"
                 + (f"Knowledge map:\n" + "\n".join(map_lines) + "\n\n" if map_lines else "")
                 + f"Question: {standalone}"}]
    parts, said_thinking = [], False
    try:
        async for kind, chunk in stream(messages, "low", 3000):
            if kind == "thinking":
                if not said_thinking:
                    said_thinking = True
                    yield {"type": "thinking"}
            else:
                parts.append(chunk)
                yield {"type": "text", "text": chunk}
    except QwenUnavailable as e:
        yield {"type": "error", "text": f"Qwen is not available ({e}). Is LM Studio running with the model loaded?"}
        return
    answer, share = check_citations("".join(parts), len(passages))
    yield {"type": "done", "answer": answer, "cited_share": round(share, 2), "fallback": share < MIN_CITED_SHARE}


def trim(card: dict, facts: int = 30) -> dict:
    """A card small enough to send with every answer; the page fetches the rest on demand."""
    seen, kept = set(), []
    for f in sorted(card["facts"], key=lambda f: FACT_ORDER.index(f["predicate"])):
        key = (f["predicate"], f["object"].lower(), f["detail"].lower())
        if key not in seen:
            seen.add(key)
            kept.append(f)
    return {**card, "facts": kept[:facts], "incoming": card["incoming"][:15]}


def _db_path():
    from handouts.ingest import db_path

    return db_path()


async def ask_once(question: str, history: Optional[list[dict]] = None, conn=None) -> dict:
    """The whole ask flow as one result, for the non-streaming endpoints and the eval."""
    result = {"question": question, "standalone": question, "searches": [], "passages": [], "cards": [],
              "answer": None, "answer_error": None, "fallback": False, "cited_share": None}
    async for event in ask(question, history, conn=conn):
        if event["type"] == "sources":
            result.update(standalone=event["question"], searches=event["searches"], passages=event["passages"],
                          cards=event.get("cards", []))
        elif event["type"] == "done":
            result.update(answer=event["answer"], fallback=event["fallback"], cited_share=event["cited_share"])
        elif event["type"] == "error":
            result["answer_error"] = event["text"]
    return result
