import re
import threading
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from handouts import ingest, source_dir, store
from handouts.retrieve import search

router = APIRouter()

QUESTION_WORDS = ("what", "how", "why", "which", "where", "when", "who", "does", "do", "is", "are", "can", "should")
SYSTEM_PROMPT = """You answer questions about VortexHealing class handouts using only the numbered sources given.
Cite sources as [n] after each claim. When you combine sources into a conclusion that none of them states,
start that sentence with "Inference:". If the sources do not answer the question, say "The handouts don't cover
this" and name the closest sources. Never add knowledge from outside the sources. Write plain prose, with short
headings when the answer has parts (what it is, where it comes from, which tools, which class)."""


class HandoutsQuery(BaseModel):
    q: str
    mode: str = "auto"
    history: list[dict] = []


class AskQuery(BaseModel):
    question: str


def wants_answer(q: str, mode: str) -> bool:
    if mode != "auto":
        return mode == "ask"
    words = q.lower().split()
    return q.strip().endswith("?") or (bool(words) and words[0] in QUESTION_WORDS) or len(words) >= 6


async def answer_from(question: str, passages: list[dict]) -> tuple[Optional[str], Optional[str]]:
    """Returns (answer, error). Citations that point at no source are removed."""
    sources = "\n\n".join(f"[{i}] {p['title']} — {p['heading_path'] or 'start'}\n{p['text']}"
                          for i, p in enumerate(passages, 1))
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(f"{settings.LM_STUDIO_URL}/chat/completions", json={
                "model": settings.QWEN_MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                             {"role": "user", "content": f"Sources:\n\n{sources}\n\nQuestion: {question}"}],
                "temperature": 0.2, "max_tokens": 3000, "reasoning_effort": "low"})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"] or ""
    except (httpx.HTTPError, KeyError, ValueError) as e:
        return None, f"Qwen is not available ({type(e).__name__}). Is LM Studio running with the model loaded?"
    valid = range(1, len(passages) + 1)
    return re.sub(r"\[(\d+)\]", lambda m: m.group(0) if int(m.group(1)) in valid else "", text).strip(), None


@router.post("/handouts/query")
async def query_handouts(query: HandoutsQuery):
    asked = wants_answer(query.q, query.mode)
    # Story 2 rewrites follow-ups properly; until then the previous question gives the search its context.
    previous = [h.get("q", "") for h in query.history[-1:]]
    passages = search(" ".join([*previous, query.q]), limit=10)
    answer, error = (await answer_from(query.q, passages[:8])) if asked and passages else (None, None)
    if asked and not passages:
        answer = "The handouts don't cover this: nothing matched the question."
    return {"query": query.q, "mode": "ask" if asked else "search", "passages": passages, "cards": [],
            "answer": answer, "answer_error": error}


@router.get("/handouts/search")
async def search_handouts(q: str):
    return {"query": q, "results": search(q, limit=10)}


@router.post("/handouts/ask")
async def ask_handouts(query: AskQuery):
    passages = search(query.question, limit=8)
    answer, error = await answer_from(query.question, passages) if passages else (None, None)
    return {"question": query.question, "answer": answer or error, "passages": passages}


@router.get("/handouts/status")
async def handouts_status():
    if not settings.HANDOUTS_DIR:
        return {"configured": False, "scanning": False}
    conn = store.connect(ingest.db_path())
    try:
        return {"configured": True, "scanning": ingest.is_running(), "last_scan": store.get_meta(conn, "last_scan"),
                **store.counts(conn)}
    finally:
        conn.close()


@router.post("/handouts/rescan")
async def rescan_handouts():
    if ingest.is_running():
        return {"started": False, "reason": "a scan is already running"}
    threading.Thread(target=ingest.run_quietly, daemon=True).start()
    return {"started": True}


@router.get("/handouts/file/{document_id}")
async def handout_file(document_id: int):
    conn = store.connect(ingest.db_path())
    try:
        row = conn.execute("select path from documents where id = ?", (document_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(404, "No such handout")
    root = source_dir().resolve()
    path = (root / row["path"]).resolve()
    if root not in path.parents or not path.exists():
        raise HTTPException(404, "Handout file not found")
    # The PDF of the same version reads better in a browser than the .doc it was indexed from.
    pdf = path.with_suffix(".pdf")
    return FileResponse(pdf if pdf.exists() else path)
