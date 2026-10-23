import hashlib

import numpy as np
import pytest

from app.core.config import settings
from handouts import ingest, retrieve, store

WORDS = "Roses need sun and water every single day to thrive in the garden bed. "


def fake_embed(texts, kind):
    """Deterministic bag-of-words vectors so tests need no LM Studio."""
    v = np.zeros((len(texts), 64), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().split():
            v[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)


@pytest.fixture
def kb(tmp_path, monkeypatch):
    src, data = tmp_path / "src", tmp_path / "kb"
    src.mkdir()
    monkeypatch.setattr(settings, "HANDOUTS_DIR", str(src))
    monkeypatch.setattr(settings, "HANDOUTS_KB_DIR", str(data))
    monkeypatch.setattr(ingest, "extract_text", lambda p: p.read_text())
    monkeypatch.setattr(ingest, "embed", fake_embed)
    monkeypatch.setattr(retrieve, "embed", fake_embed)
    retrieve._vectors.clear()
    return src


def write(src, name, body):
    (src / name).write_text(f"Garden Review\n\nPlanting\n{body}\n")


def scan():
    return ingest.run(out=lambda s: None)


def conn():
    return store.connect(ingest.db_path())


def test_unchanged_files_are_skipped_on_the_next_scan(kb):
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    assert scan()["indexed"] == 1
    again = scan()
    assert again["indexed"] == 0 and again["unchanged"] == 1


def test_a_changed_file_replaces_its_old_text(kb):
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    scan()
    write(kb, "Garden-Review-1.doc", "Ferns prefer deep shade and damp soil. " * 5)
    assert scan()["indexed"] == 1
    texts = [p["text"] for p in retrieve.search("ferns roses", conn=conn())]
    assert texts and all("Ferns" in t and "Roses" not in t for t in texts)


def test_a_new_version_retires_the_old_one(kb):
    write(kb, "Garden-Review-1.doc", "Old advice about tulips. " * 20)
    scan()
    write(kb, "Garden-Review-2.doc", "New advice about tulips and bulbs. " * 20)
    scan()
    c = conn()
    assert store.get_document(c, "Garden-Review-1.doc")["status"] == "RETIRED"
    assert {p["path"] for p in retrieve.search("tulips", conn=c)} == {"Garden-Review-2.doc"}


def test_identical_text_under_two_names_is_indexed_once(kb):
    write(kb, "Dragon-Story-1.doc", WORDS * 3)
    write(kb, "Base-Dragon-Story-1.doc", WORDS * 3)
    assert scan()["identical_text"] == 1
    assert store.counts(conn())["documents"] == 1


def test_chunks_wait_for_embeddings_when_lm_studio_is_down(kb, monkeypatch):
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    monkeypatch.setattr(ingest, "embed", lambda texts, kind: None)
    scan()
    assert store.counts(conn())["chunks_without_embeddings"] > 0
    monkeypatch.setattr(ingest, "embed", fake_embed)
    scan()
    assert store.counts(conn())["chunks_without_embeddings"] == 0


def test_a_file_removed_from_the_folder_is_retired(kb):
    write(kb, "Garden-Review-1.doc", WORDS * 5)
    scan()
    (kb / "Garden-Review-1.doc").unlink()
    scan()
    assert store.get_document(conn(), "Garden-Review-1.doc")["status"] == "RETIRED"


def test_abbreviations_are_harvested_only_when_initials_match():
    found = ingest.harvest_abbreviations(
        "Channel Multi-Frequency transmission (MF) daily. The Rose Garden (RG) opens. Water Things (MF) too.")
    assert ("RG", "Rose Garden") in found
    assert ("MF", "Multi-Frequency transmission") in found  # lower-case words do not count as initials
    assert not any("Water" in x for _, x in found)
