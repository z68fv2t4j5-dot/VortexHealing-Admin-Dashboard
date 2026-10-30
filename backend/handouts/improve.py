"""The improvement loop: test questions, background runs of them, Daniel's marks, and note drafts.

Everything lives in HANDOUTS_KB_DIR/eval: questions.yaml (the test questions) and runs/<id>.json (one
file per run, written after every answer so progress survives a restart). A run asks each question as the
page would; Daniel marks each answer Right, Partly or Wrong; for a correction Qwen drafts a teacher note
in Daniel's words, which he edits and saves in the note editor.
"""
import asyncio
import json
import logging
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import yaml

from handouts import kb_dir, knowledge, store
from handouts.answer import QwenUnavailable, ask_once, complete

logger = logging.getLogger(__name__)
_running = threading.Lock()

MARKS = ("Right", "Partly", "Wrong")
QUESTION_FIELDS = ("q", "expect", "history", "answer_should_say", "note")
HEADER = ("# Daniel's test questions for the handouts knowledge base. Edited from the Improve tab on the Handouts page.\n"
          "# Lives outside the public repo on purpose; never commit it.\n"
          "# expect: handout families that should be found (optional); answer_should_say: what a right answer contains (optional).\n\n")

DRAFT_PROMPT = """A teacher has corrected an answer about VortexHealing class handouts. Turn the teacher's correction
into a short teacher note that will be read later on its own, without the question or the answer beside it.
The note must name what it is about: take the subject (a tool, class or kind of conditioning) from the question
or the answer, never "it" or "this". Keep the teacher's words and facts; add no other facts.
Example: question "what is MIJI mantra good for?", correction "one more - to connect with Merlin in meditation"
-> {"topic": "MIJI for meditation", "body": "MIJI can also be used to connect with Merlin in meditation."}
Reply with JSON only: {"topic": "a few words", "body": "the note"}"""


def eval_dir() -> Path:
    return kb_dir() / "eval"


def runs_dir() -> Path:
    return eval_dir() / "runs"


# --- test questions ---------------------------------------------------------------------------

def questions() -> list[dict]:
    f = eval_dir() / "questions.yaml"
    loaded = yaml.safe_load(f.read_text()) if f.exists() else []
    return [q for q in loaded or [] if isinstance(q, dict) and q.get("q")]


def _write_questions(items: list[dict]) -> None:
    eval_dir().mkdir(parents=True, exist_ok=True)
    (eval_dir() / "questions.yaml").write_text(HEADER + yaml.safe_dump(items, sort_keys=False, allow_unicode=True, width=120))


def clean_question(data: dict) -> dict:
    """Only known fields; empty optional ones dropped; lists kept as lists."""
    q = str(data.get("q") or "").strip()
    if not q:
        raise ValueError("a test question needs some text")
    out: dict = {"q": q}
    for key in ("expect", "history"):
        values = [str(v).strip() for v in data.get(key) or [] if str(v).strip()]
        if values:
            out[key] = values
    for key in ("answer_should_say", "note"):
        if str(data.get(key) or "").strip():
            out[key] = str(data[key]).strip()
    return out


def add_question(data: dict) -> list[dict]:
    items = questions() + [clean_question(data)]
    _write_questions(items)
    return items


def update_question(index: int, data: dict) -> list[dict]:
    items = questions()
    if not 0 <= index < len(items):
        raise IndexError(index)
    items[index] = clean_question(data)
    _write_questions(items)
    return items


def delete_question(index: int) -> list[dict]:
    items = questions()
    if not 0 <= index < len(items):
        raise IndexError(index)
    del items[index]
    _write_questions(items)
    return items


# --- runs --------------------------------------------------------------------------------------

def is_running() -> bool:
    return _running.locked()


def run_path(run_id: str) -> Path:
    if not re.fullmatch(r"\d{8}-\d{6}", run_id):
        raise ValueError(f"not a run id: {run_id!r}")
    return runs_dir() / f"{run_id}.json"


def load_run(run_id: str) -> dict:
    return json.loads(run_path(run_id).read_text())


def _save_run(run: dict) -> None:
    runs_dir().mkdir(parents=True, exist_ok=True)
    tmp = run_path(run["id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=1))
    tmp.replace(run_path(run["id"]))


def summary(run: dict) -> dict:
    items = run["items"]
    answered = [i for i in items if i.get("seconds") is not None]
    counts = {m: sum(1 for i in items if i.get("mark") == m) for m in MARKS}
    return {"id": run["id"], "started": run["started"], "finished": run.get("finished"), "status": run["status"],
            "total": len(items), "answered": len(answered), **counts,
            "unmarked": sum(1 for i in answered if not i.get("mark")),
            "average_seconds": round(sum(i["seconds"] for i in answered) / len(answered)) if answered else None}


def list_runs() -> list[dict]:
    if not runs_dir().exists():
        return []
    return [summary(json.loads(f.read_text())) for f in sorted(runs_dir().glob("*.json"), reverse=True)]


def start_run(only: Optional[list[int]] = None) -> Optional[str]:
    """Starts a run in the background and returns its id; None when one is already running."""
    if not _running.acquire(blocking=False):
        return None
    run = new_run(only)
    threading.Thread(target=_run_in_background, args=(run,), daemon=True).start()
    return run["id"]


def new_run(only: Optional[list[int]] = None) -> dict:
    chosen = [(n, q) for n, q in enumerate(questions(), 1) if not only or n in only]
    run = {"id": datetime.now().strftime("%Y%m%d-%H%M%S"), "started": store._now(), "status": "running",
           "items": [{"n": n, "q": q["q"], "history": q.get("history", []), "should_say": q.get("answer_should_say"),
                      "seconds": None} for n, q in chosen]}
    _save_run(run)
    return run


def _run_in_background(run: dict) -> None:
    try:
        answer_all(run, out=logger.info)
    except Exception:
        logger.exception("Test run %s failed", run["id"])
        run["status"] = "failed"
        _save_run(run)
    finally:
        _running.release()


def answer_all(run: dict, out: Callable[[str], None] = print) -> dict:
    """Asks every question of the run, saving after each; a follow-up gets the answers before it."""
    answers: dict[str, str] = {}
    for item in run["items"]:
        history = [{"q": h, "answer": answers.get(h, "")} for h in item["history"]]
        start = time.time()
        result = asyncio.run(ask_once(item["q"], history))
        item.update(seconds=round(time.time() - start), standalone=result["standalone"],
                    searches=result["searches"], answer=result["answer"], answer_error=result["answer_error"],
                    fallback=result["fallback"],
                    sources=[f"{p['title']} — {p['heading_path'] or 'opening section'}" for p in result["passages"]],
                    cards=[c["name"] for c in result["cards"]])
        answers[item["q"]] = result["answer"] or ""
        out(f"{item['n']:2}. {item['seconds']:4}s  {item['q']}")
        _save_run(run)
    run.update(status="done", finished=store._now())
    _save_run(run)
    return run


def mark(run_id: str, n: int, value: Optional[str], note: Optional[str] = None) -> dict:
    if value not in (*MARKS, None):
        raise ValueError(f"a mark is one of {', '.join(MARKS)}")
    run = load_run(run_id)
    item = next((i for i in run["items"] if i["n"] == n), None)
    if item is None:
        raise IndexError(n)
    item["mark"] = value
    if note is not None:
        item["note"] = note.strip()
    _save_run(run)
    return item


def note_saved(run_id: str, n: int, note_file: str) -> None:
    run = load_run(run_id)
    for item in run["items"]:
        if item["n"] == n:
            item["note_file"] = note_file
    _save_run(run)


# --- note drafts ---------------------------------------------------------------------------------

async def draft_note(run_id: str, n: int) -> dict:
    """Qwen rewrites Daniel's correction as a self-contained note; the entries come from the knowledge map."""
    from handouts.ingest import db_path

    item = next((i for i in load_run(run_id)["items"] if i["n"] == n), None)
    if item is None:
        raise IndexError(n)
    correction = (item.get("note") or "").strip()
    if not correction:
        raise ValueError("write what is wrong or missing first")
    question = item.get("standalone") or item["q"]
    conn = store.connect(db_path())
    try:
        entities = [conn.execute("select name from entities where id = ?", (i,)).fetchone()[0]
                    for i in knowledge.find_entities(conn, question, limit=4)]
    finally:
        conn.close()
    draft = {"topic": question.rstrip("?").strip().capitalize(), "body": correction, "entities": entities}
    try:
        context = (item.get("answer") or "")[:800]
        reply = await complete([{"role": "system", "content": DRAFT_PROMPT},
                                {"role": "user", "content": f"Question: {question}\nAnswer given: {context}\n"
                                                            f"Teacher's correction: {correction}"}],
                               "none", 400)
        parsed = json.loads(reply[reply.find("{"):reply.rfind("}") + 1])
        if str(parsed.get("body") or "").strip():
            draft["body"] = str(parsed["body"]).strip()
        if str(parsed.get("topic") or "").strip():
            draft["topic"] = str(parsed["topic"]).strip()
    except (QwenUnavailable, ValueError):
        pass  # Daniel's own words are a good note too
    return draft


# --- search check --------------------------------------------------------------------------------

def search_check() -> dict:
    """How many questions with expected handouts find one among the top 5 handout passages (no Qwen)."""
    from handouts.retrieve import search

    rows = []
    for n, item in enumerate(questions(), 1):
        if not item.get("expect"):
            continue
        query = " ".join([*item.get("history", []), item["q"]])
        found = [p["family"] for p in search(query, limit=10) if p["source_kind"] == "handout"][:5]
        rows.append({"n": n, "q": item["q"], "hit": bool({f.lower() for f in item["expect"]} & set(found)),
                     "found": list(dict.fromkeys(found))})
    return {"hits": sum(r["hit"] for r in rows), "total": len(rows), "questions": rows}
