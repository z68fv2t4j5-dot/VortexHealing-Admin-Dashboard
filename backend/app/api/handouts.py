import json
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from handouts import ingest, source_dir, store
from handouts.answer import ask, ask_once
from handouts.retrieve import search

router = APIRouter()

QUESTION_WORDS = ("what", "how", "why", "which", "where", "when", "who", "does", "do", "is", "are", "can", "should")


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


@router.post("/handouts/query")
async def query_handouts(query: HandoutsQuery):
    if not wants_answer(query.q, query.mode):
        return {"query": query.q, "mode": "search", "passages": search(query.q, limit=10), "cards": [],
                "answer": None, "answer_error": None}
    result = await ask_once(query.q, query.history)
    return {"query": query.q, "mode": "ask", "cards": [], **result}


@router.post("/handouts/query/stream")
async def query_handouts_stream(query: HandoutsQuery):
    """Newline-delimited JSON events, so the page can show passages at once and the answer as it is written."""
    async def events():
        if wants_answer(query.q, query.mode):
            async for event in ask(query.q, query.history):
                yield json.dumps(event) + "\n"
        else:
            yield json.dumps({"type": "sources", "question": query.q, "rewritten": False, "searches": [],
                              "passages": search(query.q, limit=10)}) + "\n"
            yield json.dumps({"type": "done", "answer": None}) + "\n"
    return StreamingResponse(events(), media_type="application/x-ndjson")


@router.get("/handouts/search")
async def search_handouts(q: str):
    return {"query": q, "results": search(q, limit=10)}


@router.post("/handouts/ask")
async def ask_handouts(query: AskQuery):
    result = await ask_once(query.question)
    return {"question": query.question, "answer": result["answer"] or result["answer_error"],
            "passages": result["passages"]}


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
