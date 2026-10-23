from handouts import ingest, retrieve, store
from handouts.retrieve import expand, fuse

from tests.test_handouts_ingest import kb, scan, write  # noqa: F401  (kb is a fixture)


def test_rrf_prefers_an_item_ranked_well_in_both_lists():
    fused = fuse([[1, 2, 3], [4, 2, 5]])
    assert max(fused, key=fused.get) == 2  # second in both beats first in only one
    assert fused[1] > fused[3]


def test_abbreviations_expand_to_their_long_form():
    assert expand("what is MF for", {"MF": ["Multi-Frequency"]}) == "what is MF for Multi-Frequency"
    assert expand("mf structures", {"MF": ["Multi-Frequency"]}).endswith("Multi-Frequency")


def test_glossary_file_wins_over_harvested_abbreviations(kb):
    write(kb, "Tools-Review-1.doc", "The Quiet Engine (QE) runs softly. " * 10)
    scan()
    c = store.connect(ingest.db_path())
    assert retrieve.glossary(c)["QE"] == ["Quiet Engine"]
    (retrieve.kb_dir() / "glossary.yaml").write_text("QE: [Quantum Elixir]\nlevels:\n  - x\n")
    assert retrieve.glossary(c)["QE"] == ["Quantum Elixir"]


def test_searching_an_abbreviation_finds_the_long_form(kb):
    write(kb, "Tools-Review-1.doc", "Channel Multi-Frequency into the heart for ten minutes. " * 10)
    write(kb, "Other-Notes-1.doc", "Gardens need water every day. " * 10)
    scan()
    (retrieve.kb_dir() / "glossary.yaml").write_text("MF: [Multi-Frequency]\n")
    hits = retrieve.search("MF", conn=store.connect(ingest.db_path()))
    assert hits and hits[0]["path"] == "Tools-Review-1.doc"


def test_at_most_three_passages_per_handout(kb):
    write(kb, "Long-Review-1.doc", "Tulips bloom in spring sunshine. " * 600)
    write(kb, "Short-Review-1.doc", "Tulips also need cold winters. " * 10)
    scan()
    hits = retrieve.search("tulips", limit=10, conn=store.connect(ingest.db_path()))
    assert sum(h["path"] == "Long-Review-1.doc" for h in hits) == 3
    assert any(h["path"] == "Short-Review-1.doc" for h in hits)


def test_keyword_search_alone_works_without_embeddings(kb, monkeypatch):
    write(kb, "Tools-Review-1.doc", "Merlin structures bridge energy deeply. " * 10)
    scan()
    monkeypatch.setattr(retrieve, "embed", lambda texts, kind: None)
    hits = retrieve.search("structures", conn=store.connect(ingest.db_path()))
    assert hits and hits[0]["path"] == "Tools-Review-1.doc"
