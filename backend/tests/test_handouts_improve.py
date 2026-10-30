import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import handouts as api
from handouts import answer, improve

from tests.test_handouts_answer import lm  # noqa: F401  (fixture)
from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)
from tests.test_handouts_knowledge import mapped  # noqa: F401  (fixture)


def fake_ask(answers):
    """Stands in for ask_once: answers from a dict, raising for questions mapped to an exception."""
    async def ask_once(question, history=None, conn=None, quick=False):
        reply = answers[question]
        if isinstance(reply, Exception):
            raise reply
        return {"question": question, "standalone": question + (" (follow-up)" if history else ""), "searches": [],
                "passages": [{"title": "Rose Review", "heading_path": "Planting"}], "cards": [{"name": "Rose Structure"}],
                "answer": reply, "answer_error": None, "fallback": False, "cited_share": 1.0}
    return ask_once


def test_questions_add_edit_delete_and_keep_their_fields(kb):  # noqa: F811
    improve.add_question({"q": " what is a rose? ", "expect": ["Rose-Review", " "], "note": "keep me", "history": []})
    improve.add_question({"q": "and its thorns?", "history": ["what is a rose?"], "answer_should_say": "they protect"})
    assert improve.questions() == [{"q": "what is a rose?", "expect": ["Rose-Review"], "note": "keep me"},
                                   {"q": "and its thorns?", "history": ["what is a rose?"], "answer_should_say": "they protect"}]
    improve.update_question(0, {"q": "what is a red rose?"})
    assert improve.questions()[0] == {"q": "what is a red rose?"}
    improve.delete_question(1)
    assert [q["q"] for q in improve.questions()] == ["what is a red rose?"]
    assert (improve.eval_dir() / "questions.yaml").read_text().startswith("# Daniel's test questions")
    with pytest.raises(ValueError):
        improve.add_question({"q": "  "})
    with pytest.raises(IndexError):
        improve.delete_question(5)


def test_a_run_answers_every_question_and_follow_ups_get_context(kb, monkeypatch):  # noqa: F811
    improve.add_question({"q": "what is a rose?"})
    improve.add_question({"q": "and its thorns?", "history": ["what is a rose?"]})
    monkeypatch.setattr(improve, "ask_once", fake_ask({"what is a rose?": "A flower [1].", "and its thorns?": "Spikes [1]."}))
    run = improve.answer_all(improve.new_run(), out=lambda s: None)
    saved = improve.load_run(run["id"])
    assert saved["status"] == "done" and [i["answer"] for i in saved["items"]] == ["A flower [1].", "Spikes [1]."]
    assert saved["items"][1]["standalone"].endswith("(follow-up)")
    assert saved["items"][0]["sources"] == ["Rose Review — Planting"] and saved["items"][0]["cards"] == ["Rose Structure"]
    s = improve.summary(saved)
    assert (s["answered"], s["unmarked"], s["Right"]) == (2, 2, 0)


def test_a_failing_answer_marks_the_run_failed_and_keeps_what_was_answered(kb, monkeypatch):  # noqa: F811
    improve.add_question({"q": "first"})
    improve.add_question({"q": "second"})
    monkeypatch.setattr(improve, "ask_once", fake_ask({"first": "Fine.", "second": RuntimeError("boom")}))
    improve._running.acquire()
    run = improve.new_run()
    improve._run_in_background(run)
    saved = improve.load_run(run["id"])
    assert saved["status"] == "failed" and saved["items"][0]["answer"] == "Fine."
    assert not improve.is_running()


def test_only_one_run_at_a_time(kb, monkeypatch):  # noqa: F811
    improve.add_question({"q": "first"})
    monkeypatch.setattr(improve.threading, "Thread", lambda target, args, daemon: type("T", (), {"start": lambda s: None})())
    assert improve.start_run() is not None
    assert improve.start_run() is None
    improve._running.release()


def test_marks_are_validated_and_saved(kb, monkeypatch):  # noqa: F811
    improve.add_question({"q": "first"})
    monkeypatch.setattr(improve, "ask_once", fake_ask({"first": "Fine."}))
    run = improve.answer_all(improve.new_run(), out=lambda s: None)
    improve.mark(run["id"], 1, "Partly", "  missing the thorns ")
    item = improve.load_run(run["id"])["items"][0]
    assert (item["mark"], item["note"]) == ("Partly", "missing the thorns")
    assert improve.summary(improve.load_run(run["id"]))["Partly"] == 1
    with pytest.raises(ValueError):
        improve.mark(run["id"], 1, "Maybe")
    with pytest.raises(IndexError):
        improve.mark(run["id"], 9, "Right")
    with pytest.raises(ValueError):
        improve.run_path("../../glossary")


def test_a_draft_keeps_daniels_words_and_links_the_questions_entries(mapped, monkeypatch, lm):  # noqa: F811
    improve.add_question({"q": "what does the rose structure release?"})
    monkeypatch.setattr(improve, "ask_once", fake_ask({"what does the rose structure release?": "Knots."}))
    run = improve.answer_all(improve.new_run(), out=lambda s: None)
    with pytest.raises(ValueError):
        asyncio.run(improve.draft_note(run["id"], 1))  # no correction written yet
    improve.mark(run["id"], 1, "Partly", "also thorn knots, in about 10 min")
    lm(helper=json.dumps({"topic": "Rose structure releases", "body": "The rose structure also releases thorn knots, in about 10 min."}))
    draft = asyncio.run(improve.draft_note(run["id"], 1))
    assert draft == {"topic": "Rose structure releases", "body": "The rose structure also releases thorn knots, in about 10 min.",
                     "entities": ["Rose Structure"]}
    lm(fail=True)
    assert asyncio.run(improve.draft_note(run["id"], 1))["body"] == "also thorn knots, in about 10 min"


def test_search_check_counts_only_questions_with_expected_handouts(kb):  # noqa: F811
    write(kb, "Rose-Review-1.doc", "Roses need sun every day. " * 20)
    scan()
    improve.add_question({"q": "roses sun", "expect": ["rose-review"]})
    improve.add_question({"q": "no expectation here"})
    assert improve.search_check()["hits"] == 1 and improve.search_check()["total"] == 1


def test_api_for_the_improve_tab(kb, monkeypatch):  # noqa: F811
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    client = TestClient(app)
    assert client.post("/api/handouts/eval/questions", json={"q": " "}).status_code == 400
    assert len(client.post("/api/handouts/eval/questions", json={"q": "what is a rose?"}).json()["questions"]) == 1
    assert client.put("/api/handouts/eval/questions/0", json={"q": "what is a red rose?"}).json()["questions"][0]["q"] == "what is a red rose?"
    assert client.put("/api/handouts/eval/questions/7", json={"q": "x"}).status_code == 404
    monkeypatch.setattr(improve, "ask_once", fake_ask({"what is a red rose?": "A flower."}))
    run = improve.answer_all(improve.new_run(), out=lambda s: None)
    assert client.get("/api/handouts/eval/runs").json()["runs"][0]["answered"] == 1
    assert client.get(f"/api/handouts/eval/runs/{run['id']}").json()["summary"]["total"] == 1
    assert client.get("/api/handouts/eval/runs/nope").status_code == 404
    assert client.put(f"/api/handouts/eval/runs/{run['id']}/items/1", json={"mark": "Right"}).json()["mark"] == "Right"
    assert client.put(f"/api/handouts/eval/runs/{run['id']}/items/1", json={"mark": "Meh"}).status_code == 400
    assert client.put(f"/api/handouts/eval/runs/{run['id']}/items/4", json={"mark": "Right"}).status_code == 404
    assert client.post(f"/api/handouts/eval/runs/{run['id']}/items/1/draft-note").status_code == 400
    assert client.post(f"/api/handouts/eval/runs/{run['id']}/items/9/draft-note").status_code == 404
    client.post(f"/api/handouts/eval/runs/{run['id']}/items/1/note-saved", json={"file": "2026-01-01-x.md"})
    assert improve.load_run(run["id"])["items"][0]["note_file"] == "2026-01-01-x.md"
    started = []
    monkeypatch.setattr(improve, "start_run", lambda only=None: started.append(only) or "20260101-000000")
    assert client.post("/api/handouts/eval/runs", json={"only": [1]}).json() == {"started": True, "id": "20260101-000000"}
    monkeypatch.setattr(improve, "start_run", lambda only=None: None)
    assert client.post("/api/handouts/eval/runs", json={}).json()["started"] is False
    assert started == [[1]]
    assert client.delete("/api/handouts/eval/questions/0").json()["questions"] == []
    assert client.delete("/api/handouts/eval/questions/0").status_code == 404
    assert client.get("/api/handouts/eval/search-check").json()["total"] == 0


def test_quick_answers_skip_the_split_and_think_less(mapped, lm):  # noqa: F811
    fake = lm(reply="The rose structure releases thorn knots [1].", helper='["a", "b"]')
    events = asyncio.run(_collect(answer.ask("where does the thorn knot come from and what releases it?", conn=mapped, quick=True)))
    assert events[0]["searches"] == [] and len(events[0]["passages"]) <= answer.QUICK_SOURCES + answer.QUICK_EVIDENCE + answer.MAX_NOTES
    streamed = [c for c in fake.calls if c.get("stream")][0]
    assert streamed["reasoning_effort"] == "none" and "at most 120 words" in streamed["messages"][0]["content"]
    assert not [c for c in fake.calls if not c.get("stream")]  # no split call
    assert api.wants_answer("rose", "quick") is True


async def _collect(gen):
    return [e async for e in gen]
