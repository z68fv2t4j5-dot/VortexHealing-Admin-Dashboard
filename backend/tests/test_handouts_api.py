import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import handouts as api
from app.core.config import settings
from handouts import answer, ingest

from tests.test_handouts_answer import lm  # noqa: F401  (fixture)
from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)


@pytest.fixture
def client(kb):  # noqa: F811
    write(kb, "Tools-Review-3.doc", "Merlin structures bridge energy into the heart. " * 20)
    (kb / "Tools-Review-3.pdf").write_bytes(b"%PDF-1.4 fake")
    scan()
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    return TestClient(app)


@pytest.mark.parametrize("q, mode, asked", [
    ("merlin structures", "auto", False),
    ("what are merlin structures?", "auto", True),
    ("how do structures work", "auto", True),
    ("what are merlin structures?", "search", False),
    ("merlin", "ask", True),
])
def test_auto_mode_answers_questions_and_searches_terms(q, mode, asked):
    assert api.wants_answer(q, mode) is asked


def test_search_mode_returns_passages_without_calling_qwen(client, monkeypatch):
    monkeypatch.setattr(answer.httpx, "AsyncClient", None)  # any call to Qwen would crash
    data = client.post("/api/handouts/query", json={"q": "merlin structures", "mode": "search"}).json()
    assert data["mode"] == "search" and data["answer"] is None
    assert data["passages"][0]["path"] == "Tools-Review-3.doc"


def test_ask_cites_sources_and_drops_citations_to_missing_ones(client, lm):  # noqa: F811
    lm(reply="Merlin structures bridge energy into the heart [1] and also [9].")
    data = client.post("/api/handouts/query", json={"q": "what do merlin structures do?"}).json()
    assert data["mode"] == "ask"
    assert "[1]" in data["answer"] and "[9]" not in data["answer"]


def test_the_stream_sends_passages_before_the_answer(client, lm):  # noqa: F811
    lm(reply="Merlin structures bridge energy into the heart [1].")
    with client.stream("POST", "/api/handouts/query/stream", json={"q": "what do merlin structures do?"}) as r:
        events = [json.loads(line) for line in r.iter_lines() if line]
    assert events[0]["type"] == "sources" and events[0]["passages"]
    assert events[-1]["type"] == "done" and "[1]" in events[-1]["answer"]
    with client.stream("POST", "/api/handouts/query/stream", json={"q": "merlin", "mode": "search"}) as r:
        events = [json.loads(line) for line in r.iter_lines() if line]
    assert [e["type"] for e in events] == ["sources", "done"]


def test_ask_reports_qwen_down_but_still_returns_passages(client, lm):  # noqa: F811
    lm(fail=True)
    data = client.post("/api/handouts/query", json={"q": "what do merlin structures do?"}).json()
    assert data["answer"] is None and "LM Studio" in data["answer_error"]
    assert data["passages"]
    old = client.post("/api/handouts/ask", json={"question": "what do merlin structures do?"}).json()
    assert "LM Studio" in old["answer"]


def test_a_question_nothing_matches_says_so(client, monkeypatch):
    # With embeddings the nearest passages always come back; keyword search alone can find nothing.
    from handouts import retrieve
    monkeypatch.setattr(retrieve, "embed", lambda texts, kind: None)
    data = client.post("/api/handouts/query", json={"q": "zebra quokka?"}).json()
    assert data["passages"] == [] and "don't cover" in data["answer"]


def test_follow_up_uses_the_previous_question(client):
    data = client.post("/api/handouts/query", json={
        "q": "zebra?", "mode": "search", "history": [{"q": "merlin structures", "answer": "x"}]}).json()
    assert data["passages"]


def test_old_search_endpoint_still_works(client):
    assert client.get("/api/handouts/search", params={"q": "merlin"}).json()["results"]


def test_status_counts_and_unconfigured(client, monkeypatch):
    data = client.get("/api/handouts/status").json()
    assert data["configured"] and data["documents"] == 1 and data["scanning"] is False
    monkeypatch.setattr(settings, "HANDOUTS_DIR", None)
    assert client.get("/api/handouts/status").json() == {"configured": False, "scanning": False}


def test_rescan_starts_once(client, monkeypatch):
    started = []
    monkeypatch.setattr(ingest, "run_quietly", lambda: started.append(1))
    assert client.post("/api/handouts/rescan").json() == {"started": True}
    monkeypatch.setattr(ingest, "is_running", lambda: True)
    assert client.post("/api/handouts/rescan").json()["started"] is False
    assert started == [1]


def test_file_serves_the_pdf_of_the_same_version(client):
    doc_id = client.get("/api/handouts/search", params={"q": "merlin"}).json()["results"][0]["document_id"]
    r = client.get(f"/api/handouts/file/{doc_id}")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert client.get("/api/handouts/file/99999").status_code == 404


def test_file_outside_the_source_folder_is_refused(client):
    from pathlib import Path
    from handouts import store
    (Path(settings.HANDOUTS_DIR).parent / "outside.doc").write_text("not a handout")
    conn = store.connect(ingest.db_path())
    doc_id = conn.execute("select id from documents where status = 'KEEP'").fetchone()[0]
    conn.execute("update documents set path = '../outside.doc' where id = ?", (doc_id,))
    conn.commit()
    assert client.get(f"/api/handouts/file/{doc_id}").status_code == 404
