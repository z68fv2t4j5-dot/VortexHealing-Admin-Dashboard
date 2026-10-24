import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import handouts as api
from handouts import answer, ingest, knowledge, notes, retrieve, store

from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)
from tests.test_handouts_knowledge import mapped, entity_id  # noqa: F401  (mapped is a fixture)


def conn():
    return store.connect(ingest.db_path())


def test_a_note_round_trips_through_its_file(kb):  # noqa: F811
    name = notes.save("Thorn knots", "  A thorn knot is cleared at Rose class.  ", ["Thorn Knot", " "], "rose-review")
    assert name.endswith("-thorn-knots.md")
    [note] = notes.list_notes()
    assert note == {"file": name, "date": name[:10], "topic": "Thorn knots", "entities": ["Thorn Knot"],
                    "corrects": "rose-review", "body": "A thorn knot is cleared at Rose class."}
    assert notes.save("Thorn knots", "Second note.") == name.replace(".md", "-2.md")


def test_hand_written_front_matter_is_read_leniently(kb):  # noqa: F811
    notes.notes_dir().mkdir(parents=True, exist_ok=True)
    (notes.notes_dir() / "2026-01-02-x.md").write_text("---\ntopic: X\nentities: Single Name\ncorrects: null\n---\n\nBody.\n")
    (notes.notes_dir() / "plain.md").write_text("Just text, no front matter.\n")
    by_file = {n["file"]: n for n in notes.list_notes()}
    assert by_file["2026-01-02-x.md"]["entities"] == ["Single Name"]
    assert by_file["plain.md"] == {"file": "plain.md", "date": None, "topic": "", "entities": [], "corrects": None,
                                   "body": "Just text, no front matter."}


def test_notes_refuse_paths_outside_their_folder(kb):  # noqa: F811
    for bad in ("../glossary.yaml", "a/b.md", "x.txt", ""):
        with pytest.raises(ValueError):
            notes.note_path(bad)
    with pytest.raises(ValueError):
        notes.save("", "text")
    with pytest.raises(FileNotFoundError):
        notes.save("Topic", "text", name="missing.md")


def test_scans_index_new_changed_and_deleted_notes(kb):  # noqa: F811
    write(kb, "Rose-Review-1.doc", "Roses need sun every day. " * 20)
    name = notes.save("Shade roses", "Some roses grow happily in shade.")
    assert scan()["notes_changed"] == 1
    doc = store.get_document(conn(), f"notes/{name}")
    assert doc["source_kind"] == "note" and doc["title"] == "Teacher note: Shade roses" and doc["doc_date"] == name[:10]
    assert scan()["notes_changed"] == 0
    notes.save("Shade roses", "Roses never grow in shade.", name=name)
    assert ingest.refresh_notes(out=lambda s: None) == 1
    assert [p["text"] for p in retrieve.search("roses shade", conn=conn()) if p["source_kind"] == "note"] \
        == ["Roses never grow in shade."]
    notes.delete(name)
    assert ingest.refresh_notes(out=lambda s: None) == 1
    assert store.get_document(conn(), f"notes/{name}") is None


def test_a_matching_note_outranks_an_equally_matching_handout(kb, monkeypatch):  # noqa: F811
    write(kb, "Rose-Review-1.doc", "Thorn knots clear with patience. " * 20)
    notes.save("Garden tip", "Thorn knots clear with patience. " * 20)  # topic shares no words with the query
    scan()
    monkeypatch.setattr(retrieve, "embed", lambda texts, kind: None)  # keyword ranking only
    first = retrieve.search("thorn knots patience", conn=conn())
    assert first[0]["source_kind"] == "note" and first[0]["score"] > first[1]["score"]
    monkeypatch.setattr(retrieve, "NOTE_BOOST", 0.0)
    scores = {p["source_kind"]: p["score"] for p in retrieve.search("thorn knots patience", conn=conn())}
    assert scores["note"] <= scores["handout"]


def test_notes_are_not_sent_for_knowledge_extraction(kb):  # noqa: F811
    notes.save("Shade roses", "Some roses grow in shade.")
    scan()
    assert all(not r["family"].startswith("note:") for r in knowledge.pending(conn()))


def test_a_card_shows_its_notes_and_answers_bring_them_in(mapped):  # noqa: F811
    notes.save("Rose structure at Fern class", "At Fern class the rose structure takes one step, not two.",
               ["Rose Structure", "Fern Class"])
    ingest.refresh_notes(out=lambda s: None)
    card = answer.trim(knowledge.card(mapped, entity_id(mapped, "Rose Structure")))
    assert [n["topic"] for n in card["notes"]] == ["Rose structure at Fern class"]
    passages, lines = answer.add_evidence(mapped, [], [card])
    note_numbers = [i for i, p in enumerate(passages, 1) if p["source_kind"] == "note"]
    assert note_numbers and f"- Teacher note on Rose structure at Fern class [{note_numbers[0]}]" in lines
    assert answer.sources_text(passages).count("Teacher note: Rose structure at Fern class (") == 1


def test_api_adds_edits_lists_serves_and_deletes_notes(kb):  # noqa: F811
    write(kb, "Rose-Review-1.doc", "Roses need sun every day. " * 20)
    scan()
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    client = TestClient(app)
    assert client.post("/api/handouts/notes", json={"topic": " ", "body": "x"}).status_code == 400
    note = client.post("/api/handouts/notes", json={"topic": "Shade roses", "body": "Roses grow in shade.",
                                                    "entities": ["Rose"]}).json()
    assert note["entities"] == ["Rose"]
    found = client.post("/api/handouts/query", json={"q": "roses shade", "mode": "search"}).json()["passages"]
    note_passage = next(p for p in found if p["source_kind"] == "note")
    served = client.get(f"/api/handouts/file/{note_passage['document_id']}")
    assert served.status_code == 200 and "Roses grow in shade." in served.text
    assert client.put(f"/api/handouts/notes/{note['file']}", json={"topic": "Shade roses", "body": "Edited."}).json()["body"] == "Edited."
    assert client.put("/api/handouts/notes/nope.md", json={"topic": "a", "body": "b"}).status_code == 404
    assert [n["file"] for n in client.get("/api/handouts/notes").json()["notes"]] == [note["file"]]
    assert client.delete("/api/handouts/notes/..%2Fglossary.yaml").status_code == 404
    assert client.delete(f"/api/handouts/notes/{note['file']}").json() == {"deleted": note["file"]}
    assert client.get("/api/handouts/notes").json()["notes"] == []
    assert client.get(f"/api/handouts/file/{note_passage['document_id']}").status_code == 404
