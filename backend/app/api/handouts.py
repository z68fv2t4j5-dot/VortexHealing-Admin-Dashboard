import json
import threading
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from handouts import improve, ingest, knowledge, model, notes, source_dir, store
from handouts.answer import ask, ask_once, trim
from handouts.retrieve import search

router = APIRouter()

QUESTION_WORDS = ("what", "how", "why", "which", "where", "when", "who", "does", "do", "is", "are", "can", "should")


class HandoutsQuery(BaseModel):
    q: str
    mode: str = "auto"
    history: list[dict] = []


class NoteIn(BaseModel):
    topic: str
    body: str
    entities: list[str] = []
    corrects: Optional[str] = None


def wants_answer(q: str, mode: str) -> bool:
    if mode != "auto":
        return mode in ("ask", "quick")
    words = q.lower().split()
    return q.strip().endswith("?") or (bool(words) and words[0] in QUESTION_WORDS) or len(words) >= 6


def cards_for(text: str) -> list[dict]:
    conn = store.connect(ingest.db_path())
    try:
        return [trim(c) for c in (knowledge.card(conn, i) for i in knowledge.find_entities(conn, text)) if c]
    finally:
        conn.close()


@router.post("/handouts/query")
async def query_handouts(query: HandoutsQuery):
    if not wants_answer(query.q, query.mode):
        return {"query": query.q, "mode": "search", "passages": search(query.q, limit=10), "cards": cards_for(query.q),
                "answer": None, "answer_error": None}
    result = await ask_once(query.q, query.history, quick=query.mode == "quick")
    return {"query": query.q, "mode": "ask", **result}


@router.post("/handouts/query/stream")
async def query_handouts_stream(query: HandoutsQuery):
    """Newline-delimited JSON events, so the page can show passages at once and the answer as it is written."""
    async def events():
        if wants_answer(query.q, query.mode):
            async for event in ask(query.q, query.history, quick=query.mode == "quick"):
                yield json.dumps(event) + "\n"
        else:
            yield json.dumps({"type": "sources", "question": query.q, "rewritten": False, "searches": [],
                              "passages": search(query.q, limit=10), "cards": cards_for(query.q)}) + "\n"
            yield json.dumps({"type": "done", "answer": None}) + "\n"
    return StreamingResponse(events(), media_type="application/x-ndjson")


@router.get("/handouts/status")
async def handouts_status():
    if not settings.HANDOUTS_DIR:
        return {"configured": False, "scanning": False}
    conn = store.connect(ingest.db_path())
    try:
        one = lambda sql: conn.execute(sql).fetchone()[0]
        return {"configured": True, "scanning": ingest.is_running(), "last_scan": store.get_meta(conn, "last_scan"),
                **store.counts(conn),
                "knowledge": {"running": knowledge.is_running(conn), "entities": one("select count(*) from entities"),
                              "facts": one("select count(*) from facts"), "sections_unread": len(knowledge.pending(conn))}}
    finally:
        conn.close()


@router.post("/handouts/knowledge/run")
async def run_knowledge():
    conn = store.connect(ingest.db_path())
    try:
        if knowledge.is_running(conn):
            return {"started": False, "reason": "the knowledge map is already being built"}
    finally:
        conn.close()
    threading.Thread(target=knowledge.run_quietly, daemon=True).start()
    return {"started": True}


@router.get("/handouts/entities")
async def list_entities(type: Optional[str] = None, q: str = ""):
    conn = store.connect(ingest.db_path())
    try:
        return {"entities": knowledge.browse(conn, type, q),
                "types": {r[0]: r[1] for r in conn.execute("select type, count(*) from entities group by type")}}
    finally:
        conn.close()


@router.get("/handouts/entity/{entity_id}")
async def entity_card(entity_id: int):
    conn = store.connect(ingest.db_path())
    try:
        result = knowledge.card(conn, entity_id)
    finally:
        conn.close()
    if result is None:
        raise HTTPException(404, "No such entry in the knowledge map")
    return result


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
    if row["path"].startswith("notes/"):
        try:
            note = notes.note_path(row["path"].removeprefix("notes/"))
        except ValueError:
            raise HTTPException(404, "Note not found")
        if not note.exists():
            raise HTTPException(404, "Note not found")
        return FileResponse(note, media_type="text/markdown; charset=utf-8")
    root = source_dir().resolve()
    path = (root / row["path"]).resolve()
    if root not in path.parents or not path.exists():
        raise HTTPException(404, "Handout file not found")
    # The PDF of the same version reads better in a browser than the .doc it was indexed from.
    pdf = path.with_suffix(".pdf")
    return FileResponse(pdf if pdf.exists() else path)


@router.get("/handouts/notes")
async def list_notes():
    return {"notes": notes.list_notes()}


def _saved(name: str) -> dict:
    ingest.refresh_notes()
    return next(n for n in notes.list_notes() if n["file"] == name)


@router.post("/handouts/notes")
async def add_note(note: NoteIn):
    try:
        name = notes.save(note.topic, note.body, note.entities, note.corrects)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _saved(name)


@router.put("/handouts/notes/{name}")
async def edit_note(name: str, note: NoteIn):
    try:
        notes.save(note.topic, note.body, note.entities, note.corrects, name=name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError:
        raise HTTPException(404, "No such note")
    return _saved(name)


@router.delete("/handouts/notes/{name}")
async def delete_note(name: str):
    try:
        notes.delete(name)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "No such note")
    ingest.refresh_notes()
    return {"deleted": name}


# --- model readiness -----------------------------------------------------------------------------

@router.get("/handouts/model")
async def model_status():
    return model.status()


@router.post("/handouts/model/load")
async def load_model():
    return {"started": model.load()}


# --- improvement loop ----------------------------------------------------------------------------

class QuestionIn(BaseModel):
    q: str
    expect: list[str] = []
    history: list[str] = []
    answer_should_say: Optional[str] = None
    note: Optional[str] = None


class MarkIn(BaseModel):
    mark: Optional[str] = None
    note: Optional[str] = None


class RunIn(BaseModel):
    only: list[int] = []


class NoteSavedIn(BaseModel):
    file: str


@router.get("/handouts/eval/questions")
async def list_questions():
    return {"questions": improve.questions()}


@router.post("/handouts/eval/questions")
async def add_question(question: QuestionIn):
    try:
        return {"questions": improve.add_question(question.model_dump())}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/handouts/eval/questions/{index}")
async def edit_question(index: int, question: QuestionIn):
    try:
        return {"questions": improve.update_question(index, question.model_dump())}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except IndexError:
        raise HTTPException(404, "No such question")


@router.delete("/handouts/eval/questions/{index}")
async def delete_question(index: int):
    try:
        return {"questions": improve.delete_question(index)}
    except IndexError:
        raise HTTPException(404, "No such question")


@router.get("/handouts/eval/runs")
async def list_runs():
    return {"runs": improve.list_runs(), "running": improve.is_running()}


@router.post("/handouts/eval/runs")
async def start_run(body: RunIn):
    run_id = improve.start_run(body.only or None)
    if run_id is None:
        return {"started": False, "reason": "a test run is already going"}
    return {"started": True, "id": run_id}


def _run_or_404(run_id: str) -> dict:
    try:
        return improve.load_run(run_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "No such run")


@router.get("/handouts/eval/runs/{run_id}")
async def get_run(run_id: str):
    run = _run_or_404(run_id)
    return {**run, "summary": improve.summary(run)}


@router.put("/handouts/eval/runs/{run_id}/items/{n}")
async def mark_item(run_id: str, n: int, body: MarkIn):
    _run_or_404(run_id)
    try:
        return improve.mark(run_id, n, body.mark, body.note)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except IndexError:
        raise HTTPException(404, "No such question in this run")


@router.post("/handouts/eval/runs/{run_id}/items/{n}/draft-note")
async def draft_note(run_id: str, n: int):
    _run_or_404(run_id)
    try:
        return await improve.draft_note(run_id, n)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except IndexError:
        raise HTTPException(404, "No such question in this run")


@router.post("/handouts/eval/runs/{run_id}/items/{n}/note-saved")
async def note_saved(run_id: str, n: int, body: NoteSavedIn):
    _run_or_404(run_id)
    improve.note_saved(run_id, n, body.file)
    return {"ok": True}


@router.get("/handouts/eval/search-check")
async def search_check():
    return improve.search_check()
