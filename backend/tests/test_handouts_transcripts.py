"""Class transcripts in the knowledge base (invented text only, ADR-0008)."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.api import handouts as api
from handouts import ingest, retrieve, store, transcripts

from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)

WORDS = "Roses need sun and water every single day to thrive in the garden bed. "


def conn():
    return store.connect(ingest.db_path())


def tdir(tmp_path, monkeypatch):
    folder = tmp_path / "transcripts"
    folder.mkdir()
    monkeypatch.setattr(settings, "TRANSCRIPTS_DIR", str(folder))
    return folder


def client():
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    return TestClient(app)


def test_scans_index_new_changed_and_deleted_transcripts(kb, tmp_path, monkeypatch):  # noqa: F811
    folder = tdir(tmp_path, monkeypatch)
    (folder / "Ric").mkdir()
    f = folder / "Ric" / "2026-01-02 — Pruning talk.md"
    f.write_text("Today we talked about pruning thorn bushes before winter. " * 10)
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    summary = scan()
    assert summary["transcripts_changed"] == 1 and summary["transcripts"] == 1
    doc = store.get_document(conn(), "transcripts/Ric/2026-01-02 — Pruning talk.md")
    assert doc["source_kind"] == "transcript" and doc["family"] == "transcript:Ric"
    assert doc["title"] == "2026-01-02 — Pruning talk" and doc["doc_date"] == "2026-01-02"
    assert scan()["transcripts_changed"] == 0
    f.unlink()
    assert scan()["transcripts_changed"] == 1
    assert store.get_document(conn(), "transcripts/Ric/2026-01-02 — Pruning talk.md") is None


def test_private_and_tooling_folders_are_skipped(kb, tmp_path, monkeypatch):  # noqa: F811
    folder = tdir(tmp_path, monkeypatch)
    for sub in ("_other", "zoom-import", "Classes"):
        (folder / sub).mkdir()
        (folder / sub / "a.md").write_text("Watering cans hold water for the garden. " * 10)
    (folder / "_report.md").write_text("A report, not a transcript.")
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    assert scan()["transcripts"] == 1
    assert store.get_document(conn(), "transcripts/Classes/a.md") is not None
    assert store.get_document(conn(), "transcripts/_other/a.md") is None
    assert store.get_document(conn(), "transcripts/zoom-import/a.md") is None
    assert store.get_document(conn(), "transcripts/_report.md") is None


def test_default_search_excludes_transcripts(kb, tmp_path, monkeypatch):  # noqa: F811
    folder = tdir(tmp_path, monkeypatch)
    (folder / "talk.md").write_text("Mulberry trees fruit in late spring, as I said in class. " * 10)
    write(kb, "Garden-Review-1.doc", "Mulberry trees fruit in late spring, says the handout. " * 10)
    scan()
    kinds = {p["source_kind"] for p in retrieve.search("mulberry trees", conn=conn())}
    assert kinds == {"handout"}
    only = retrieve.search("mulberry trees", conn=conn(), kinds={"transcript"})
    assert only and {p["source_kind"] for p in only} == {"transcript"}
    both = retrieve.search("mulberry trees", conn=conn(), kinds={"handout", "transcript"})
    assert {p["source_kind"] for p in both} == {"handout", "transcript"}
    # Transcript chunks must not occupy the semantic candidate list when they are filtered out later.
    c = conn()
    transcript_ids = {r[0] for r in c.execute(
        "select c.id from chunks c join documents d on d.id = c.document_id where d.source_kind = 'transcript'")}
    semantic = retrieve._semantic(c, "mulberry trees")
    assert semantic and not (set(semantic) & transcript_ids)


def test_query_endpoint_passes_sources_and_status_counts(kb, tmp_path, monkeypatch):  # noqa: F811
    folder = tdir(tmp_path, monkeypatch)
    (folder / "talk.md").write_text("Mulberry trees fruit in late spring, as I said in class. " * 10)
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    scan()
    c = client()
    r = c.post("/api/handouts/query", json={"q": "mulberry", "mode": "search", "sources": ["transcript"]})
    assert [p["source_kind"] for p in r.json()["passages"]] == ["transcript"]
    default = c.post("/api/handouts/query", json={"q": "mulberry", "mode": "search"}).json()["passages"]
    assert "transcript" not in {p["source_kind"] for p in default}
    assert c.get("/api/handouts/status").json()["transcripts"] == 1


def test_transcript_files_are_served_and_guarded(kb, tmp_path, monkeypatch):  # noqa: F811
    folder = tdir(tmp_path, monkeypatch)
    (folder / "talk.md").write_text("Compost heaps warm up through autumn. " * 10)
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    scan()
    doc = store.get_document(conn(), "transcripts/talk.md")
    c = client()
    r = c.get(f"/api/handouts/file/{doc['id']}")
    assert r.status_code == 200 and "Compost heaps" in r.text
    # Deleted after the last scan: the stale row answers 404, not a server error.
    (folder / "talk.md").unlink()
    assert c.get(f"/api/handouts/file/{doc['id']}").status_code == 404
    assert transcripts.file_path("../kb/kb.sqlite") is None
    assert transcripts.file_path("missing.md") is None


def test_unset_transcripts_dir_changes_nothing(kb, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "TRANSCRIPTS_DIR", None)
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    summary = scan()
    assert summary["transcripts"] == 0 and summary["transcripts_changed"] == 0
    assert retrieve.search("roses", conn=conn())
