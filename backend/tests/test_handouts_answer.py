import asyncio
import json

import httpx
import pytest

from handouts import answer, ingest, store

from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)


class FakeLMStudio:
    """An httpx transport playing LM Studio: helper calls get `helper`, the answer streams `reply`."""

    def __init__(self, reply="Merlin structures bridge energy [1].", helper="", fail=False):
        self.reply, self.helper, self.fail, self.calls = reply, helper, fail, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if self.fail:
            raise httpx.ConnectError("down")
        body = json.loads(request.content)
        self.calls.append(body)
        if body.get("stream"):
            pieces = [self.reply[i:i + 10] for i in range(0, len(self.reply), 10)]
            lines = [{"choices": [{"delta": {"reasoning_content": "hmm"}}]}]
            lines += [{"choices": [{"delta": {"content": p}}]} for p in pieces]
            text = "".join(f"data: {json.dumps(x)}\n\n" for x in lines)
            return httpx.Response(200, text=text + "data: [DONE]\n\n")
        return httpx.Response(200, json={"choices": [{"message": {"content": self.helper}}]})


REAL_CLIENT = httpx.AsyncClient


@pytest.fixture
def lm(monkeypatch):
    def install(**kwargs):
        fake = FakeLMStudio(**kwargs)
        monkeypatch.setattr(answer.httpx, "AsyncClient",
                            lambda **kw: REAL_CLIENT(transport=httpx.MockTransport(fake), **kw))
        return fake
    return install


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def indexed(kb):  # noqa: F811
    write(kb, "Tools-Review-3.doc", "Merlin structures bridge energy into the heart. " * 20)
    write(kb, "Fear-Review-2.doc", "Fear of loss comes from the karmic body and old webbing. " * 20)
    scan()
    return store.connect(ingest.db_path())


def test_a_follow_up_is_rewritten_and_a_first_question_is_not(lm):
    fake = lm(helper='"Which class clears a gremmie?"\nextra line')
    assert run(answer.rewrite("which class?", [{"q": "what is a gremmie?", "answer": "A dense structure."}])) \
        == "Which class clears a gremmie?"
    assert run(answer.rewrite("what is a gremmie?", [])) == "what is a gremmie?"
    assert len(fake.calls) == 1 and fake.calls[0]["reasoning_effort"] == "none"


@pytest.mark.parametrize("q, multipart", [
    ("what is a gremmie?", False),
    ("where does fear of abandonment come from and which tools release it?", True),
    ("does vortex change the genetic code? what does it do with genetics?", True),
    ("what role does epigenetics play in our issues?", False),
])
def test_only_multi_part_questions_are_split(q, multipart):
    assert answer.is_multipart(q) is multipart


def test_split_reads_a_json_list_and_survives_junk(lm):
    lm(helper='Sure: ["origin of fear", "tools for fear", "a", "b"]')
    assert run(answer.split("where does fear come from and which tools release it?")) == ["origin of fear", "tools for fear", "a"]
    fake = lm(helper="no list here")
    assert run(answer.split("where does fear come from and which tools release it?")) == []
    assert run(answer.split("short question?")) == []
    assert len(fake.calls) == 1  # the short question never reached Qwen


def test_citations_to_missing_sources_are_removed_and_counted():
    text, share = answer.check_citations(
        "## Heading\nThis long paragraph has a proper citation in it here [1].\n"
        "This other long paragraph cites a source that does not exist [7].", 2)
    assert "[7]" not in text and "[1]" in text
    assert share == 0.5


def test_gather_merges_searches_within_the_limit(indexed):
    passages = answer.gather("merlin structures", ["fear of loss"], conn=indexed, limit=4)
    assert {p["path"] for p in passages} == {"Tools-Review-3.doc", "Fear-Review-2.doc"}
    assert len(passages) <= 4


def test_gather_takes_at_most_three_passages_from_one_handout(kb):  # noqa: F811
    # Each search alone returns 3 passages of the long handout, different ones per search.
    # Distinct sentences, so the passages are not duplicates of each other.
    write(kb, "Long-Review-1.doc", "".join(f"Roses need sun on day {i}. " for i in range(400))
          + "".join(f"Ferns like deep shade in week {i}. " for i in range(400)))
    write(kb, "Short-Review-1.doc", "Roses and ferns share a garden bed. " * 20)
    scan()
    passages = answer.gather("roses sun", ["ferns shade"], conn=store.connect(ingest.db_path()), limit=8)
    assert sum(p["path"] == "Long-Review-1.doc" for p in passages) == 3
    assert any(p["path"] == "Short-Review-1.doc" for p in passages)


def test_repeated_text_is_given_to_qwen_once(kb):  # noqa: F811
    text = "".join(f"Thorn knots and roses, point {i}: the gardener checks bed {i * 7} at dawn. " for i in range(15))  # one passage
    write(kb, "Rose-Review-1.doc", text)
    write(kb, "Manual-2026.doc", text + "Plus one extra closing line.")  # a reprint with a small addition
    scan()
    passages = answer.gather("thorn knots roses", [], conn=store.connect(ingest.db_path()))
    assert len(passages) == 1


def test_matching_notes_come_on_top_of_the_handout_passages(kb):  # noqa: F811
    from handouts import notes
    topics = {"Alpha": "soil pH and lime", "Beta": "pruning shears and frost", "Gamma": "aphids and ladybirds"}
    for name, topic in topics.items():
        write(kb, f"{name}-Notes.doc", f"Thorn knots and roses: {topic}. " + " ".join(f"{name.lower()}{w}" for w in range(40)))
    notes.save("Thorn knots", "Thorn knots and roses: my own view.")
    scan()
    passages = answer.gather("thorn knots roses", [], conn=store.connect(ingest.db_path()), limit=2)
    assert [p["source_kind"] for p in passages] == ["note", "handout", "handout"]


def test_the_prompt_carries_daniels_glossary(kb):  # noqa: F811
    from handouts import kb_dir
    kb_dir().mkdir(parents=True, exist_ok=True)
    (kb_dir() / "glossary.yaml").write_text('LF: [LifeForm]\nXX: [?]\nYY: ["?"]\n')
    prompt = answer.system_prompt()
    assert "LF = LifeForm" in prompt and "XX" not in prompt and "YY" not in prompt


def test_ask_streams_sources_then_text_then_done(indexed, lm):
    lm(reply="Merlin structures bridge energy into the heart [1].")
    events = run(_collect(answer.ask("what are merlin structures?", conn=indexed)))
    kinds = [e["type"] for e in events]
    assert kinds[0] == "sources" and kinds[1] == "thinking" and kinds[-1] == "done"
    assert "text" in kinds and events[-1]["fallback"] is False
    assert events[-1]["answer"].startswith("Merlin structures")


def test_an_uncited_answer_falls_back_to_the_passages(indexed, lm):
    lm(reply="Merlin structures are lovely things that do many wonderful things for everyone.")
    done = run(_collect(answer.ask("what are merlin structures?", conn=indexed)))[-1]
    assert done["fallback"] is True


def test_qwen_down_still_returns_passages(indexed, lm):
    lm(fail=True)
    result = run(answer.ask_once("what are merlin structures?", [{"q": "x", "answer": "y"}], conn=indexed))
    assert result["passages"] and result["answer"] is None and "LM Studio" in result["answer_error"]


async def _collect(gen):
    return [e async for e in gen]
