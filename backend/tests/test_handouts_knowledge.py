import json
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import handouts as api
from handouts import answer, ingest, kb_dir, knowledge, store

from tests.test_handouts_answer import lm  # noqa: F401  (fixture)
from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)

READINGS = {
    "Rose Review": {
        "entities": [{"name": "Rose Structure", "type": "tool", "aliases": ["RS"], "definition": "A funnel of light."},
                     {"name": "Thorn Knot", "type": "conditioning", "definition": "A dense knot of old history."}],
        "facts": [{"subject": "Rose Structure", "predicate": "introduced_in", "object": "Rose Class", "detail": ""},
                  {"subject": "Rose Structure", "predicate": "releases", "object": "Thorn Knot", "detail": "about 10 min"},
                  {"subject": "Rose Structure", "predicate": "invented_by", "object": "Nobody"},
                  {"subject": "Rose Structure", "predicate": "done_in_class", "object": "Rose Class", "detail": "two days"}],
    },
    "Fern Review": {
        "entities": [{"name": "the rose structure", "type": "structure", "definition": "Also used here."}],
        "facts": [{"subject": "Rose Structure", "predicate": "done_in_class", "object": "Fern Class", "detail": "one session"},
                  {"subject": "MF", "predicate": "releases", "object": "Thorn Knot", "detail": ""}],
    },
}


@pytest.fixture
def mapped(kb):  # noqa: F811
    """Two invented handouts, with cached readings standing in for Qwen, then apply()."""
    write(kb, "Rose-Review-1.doc", "The rose structure releases thorn knots in the garden. " * 20)
    (kb / "Fern-Review-1.doc").write_text("Fern Review\n\nShade\n" + "Ferns use the rose structure in one session. " * 20)
    scan()
    conn = store.connect(ingest.db_path())
    (kb_dir() / "glossary.yaml").write_text("MF: [Multi-Frequency]\n")
    (kb_dir() / "handout_classes.yaml").write_text("rose-review: Rose Class\nfern-review: Fern Class\n")
    for row in conn.execute("select s.text_sha, d.path from sections s join documents d on d.id = s.document_id"):
        reading = READINGS["Rose Review" if row["path"].startswith("Rose") else "Fern Review"]
        conn.execute("insert or replace into extraction_cache(text_sha, model, result, done_at) values (?,?,?,?)",
                     (row["text_sha"], knowledge.model_name(), json.dumps(reading), "now"))
    conn.commit()
    knowledge.apply(conn)
    return conn


def entity_id(conn, name):
    return conn.execute("select id from entities where norm = ?", (knowledge.norm(name),)).fetchone()[0]


def test_names_merge_across_handouts_and_take_the_commonest_type(mapped):
    rose = mapped.execute("select * from entities where norm = 'rose structure'").fetchall()
    assert len(rose) == 1 and rose[0]["type"] in ("tool", "structure")
    assert json.loads(rose[0]["aliases"]) == ["RS"]


def test_unknown_predicates_are_dropped_and_glossary_abbreviations_merge(mapped):
    assert mapped.execute("select count(*) from facts where predicate = 'invented_by'").fetchone()[0] == 0
    assert mapped.execute("select count(*) from entities where norm = 'mf'").fetchone()[0] == 0
    assert mapped.execute("select count(*) from entities where norm = 'multi frequency'").fetchone()[0] == 1


def test_a_card_shows_the_class_comparison_with_sources(mapped):
    card = knowledge.card(mapped, entity_id(mapped, "Rose Structure"))
    assert card["introduced_in"] == ["Rose Class"]
    done = {(f["object"], f["detail"]) for f in card["facts"] if f["predicate"] == "done_in_class"}
    assert done == {("Rose Class", "two days"), ("Fern Class", "one session")}
    assert all(f["source"]["title"] for f in card["facts"])
    thorn = knowledge.card(mapped, entity_id(mapped, "Thorn Knot"))
    assert {i["subject"] for i in thorn["incoming"]} == {"Rose Structure", "Multi-Frequency"}


def test_entities_are_found_in_questions_by_name_alias_and_abbreviation(mapped):
    rose, mf = entity_id(mapped, "Rose Structure"), entity_id(mapped, "Multi-Frequency")
    assert knowledge.find_entities(mapped, "How is the Rose Structure done in each class?") == [rose]
    assert knowledge.find_entities(mapped, "what does RS do") == []  # aliases under 4 letters are ignored
    assert knowledge.find_entities(mapped, "what does MF release?") == [mf]
    assert knowledge.find_entities(mapped, "tell me about tulips") == []


@pytest.mark.parametrize("name, expected", [
    ("Multi-Frequency class", "Multi-Frequency"), ("MF", "Multi-Frequency"), ("Omega", "OMEGA & the Karmic Body"),
    ("Merlins Grace", "Merlin's Grace"), ("Argentina", None), ("Jewel", "Jewel"),
])
def test_class_names_resolve_to_the_flowchart(name, expected):
    assert knowledge.canonical_class(name, knowledge.known_classes(), {"mf": "multi frequency"}) == expected


def test_only_known_classes_are_typed_as_classes(mapped):
    reading = {"entities": [{"name": "Argentina", "type": "class", "definition": "A country."}],
               "facts": [{"subject": "Rose Structure", "predicate": "introduced_in", "object": "Jewel class"}]}
    sha = mapped.execute("select text_sha from sections limit 1").fetchone()[0]
    mapped.execute("update extraction_cache set result = ? where text_sha = ?", (json.dumps(reading), sha))
    knowledge.apply(mapped)
    assert mapped.execute("select type from entities where norm = 'argentina'").fetchone()[0] is None
    assert "Jewel" in knowledge.card(mapped, entity_id(mapped, "Rose Structure"))["introduced_in"]


def test_an_abbreviation_never_becomes_the_display_name(mapped):
    reading = {"entities": [{"name": "Rose Structure", "type": "tool", "aliases": ["RS"], "definition": "x"}],
               "facts": [{"subject": "RS", "predicate": "releases", "object": f"Knot {i}"} for i in range(6)]}
    sha = mapped.execute("select text_sha from sections limit 1").fetchone()[0]
    mapped.execute("update extraction_cache set result = ? where text_sha = ?", (json.dumps(reading), sha))
    knowledge.apply(mapped)
    assert mapped.execute("select name from entities where norm = 'rose structure'").fetchone()[0] == "Rose Structure"


def test_cached_sections_are_not_read_again(mapped):
    assert knowledge.pending(mapped) == []


def test_run_reads_pending_sections_and_survives_a_failure(kb, monkeypatch):  # noqa: F811
    write(kb, "Rose-Review-1.doc", "The rose structure releases thorn knots. " * 20)
    write(kb, "Fern-Review-1.doc", "Ferns like shade. " * 20)
    scan()
    calls = []

    async def fake_extract(text, title, heading, klass):
        calls.append(title)
        if "Fern" in text:
            raise ValueError("bad JSON")
        return READINGS["Rose Review"]

    monkeypatch.setattr(knowledge, "extract", fake_extract)
    summary = knowledge.run(out=lambda s: None)
    assert summary["read"] == 1 and summary["failed"] == 1 and summary["facts"] >= 3
    conn = store.connect(ingest.db_path())
    assert len(knowledge.pending(conn)) == 1  # the failed section waits for the next run
    assert store.get_meta(conn, "knowledge_heartbeat") is None


def test_a_recent_heartbeat_means_running(mapped):
    assert knowledge.is_running(mapped) is False
    store.set_meta(mapped, "knowledge_heartbeat", str(time.time()))
    assert knowledge.is_running(mapped) is True
    store.set_meta(mapped, "knowledge_heartbeat", str(time.time() - 3600))
    assert knowledge.is_running(mapped) is False


def test_extract_keeps_only_usable_items(lm):  # noqa: F811
    lm(helper=json.dumps({"entities": [{"name": "Rose"}, {"type": "tool"}, "junk"],
                          "facts": [{"subject": "Rose", "object": "Knot", "predicate": "releases"}, {"subject": "Rose"}]}))
    import asyncio
    result = asyncio.run(knowledge.extract("text", "Title", "Heading", None))
    assert result == {"entities": [{"name": "Rose"}], "facts": [{"subject": "Rose", "object": "Knot", "predicate": "releases"}]}


def test_answers_pull_in_the_passages_behind_key_facts(mapped):
    card = answer.trim(knowledge.card(mapped, entity_id(mapped, "Rose Structure")))
    rose_only = [p for p in answer.gather("thorn knots garden", [], conn=mapped) if p["path"].startswith("Rose")]
    passages, lines = answer.add_evidence(mapped, rose_only, [card])
    assert any(p["path"].startswith("Fern") for p in passages)  # pulled in by the Fern Class fact
    assert any("is done in Fern Class (one session) [" in ln for ln in lines)
    numbers = {int(ln.rsplit("[", 1)[1].rstrip("]")) for ln in lines}
    assert numbers <= set(range(1, len(passages) + 1))


def test_trim_removes_repeated_facts(mapped):
    card = knowledge.card(mapped, entity_id(mapped, "Rose Structure"))
    card["facts"] = card["facts"] + card["facts"]
    trimmed = answer.trim(card)
    assert len(trimmed["facts"]) == len({(f["predicate"], f["object"].lower(), f["detail"].lower()) for f in card["facts"]})


def test_api_lists_entities_and_serves_cards(mapped, monkeypatch):
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    client = TestClient(app)
    listing = client.get("/api/handouts/entities", params={"type": "conditioning"}).json()
    assert [e["name"] for e in listing["entities"]] == ["Thorn Knot"]
    rose = entity_id(mapped, "Rose Structure")
    assert client.get(f"/api/handouts/entity/{rose}").json()["introduced_in"] == ["Rose Class"]
    assert client.get("/api/handouts/entity/99999").status_code == 404
    status = client.get("/api/handouts/status").json()["knowledge"]
    assert status["entities"] >= 4 and status["sections_unread"] == 0
    started = []
    monkeypatch.setattr(knowledge, "run_quietly", lambda: started.append(1))
    assert client.post("/api/handouts/knowledge/run").json()["started"] is True
    store.set_meta(mapped, "knowledge_heartbeat", str(time.time()))
    mapped.commit()
    assert client.post("/api/handouts/knowledge/run").json()["started"] is False
    assert started == [1]
    search = client.post("/api/handouts/query", json={"q": "rose structure", "mode": "search"}).json()
    assert [c["name"] for c in search["cards"]] == ["Rose Structure"]
