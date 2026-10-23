"""One scan of the handouts folder: catalogue -> extract -> sections -> store -> embed.

Incremental: a KEEP file whose bytes are unchanged is skipped. Used by the CLI,
the backend's startup scan and the page's Rescan button.
"""
import hashlib
import logging
import os
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Callable

import yaml

from handouts import catalog, kb_dir, source_dir, store
from handouts.embed import embed
from handouts.extract import extract_text
from handouts.sections import chunk, split

logger = logging.getLogger(__name__)
_lock = threading.Lock()
EMBED_BATCH = 256


def db_path() -> Path:
    return kb_dir() / "kb.sqlite"


def is_running() -> bool:
    return _lock.locked()


def scan(root: Path) -> list[str]:
    return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, files in os.walk(root) for f in files)


def load_overrides(kb: Path) -> dict:
    f = kb / "catalog_overrides.yaml"
    return (yaml.safe_load(f.read_text()) or {}) if f.exists() else {}


def run(dry_run: bool = False, full: bool = False, out: Callable[[str], None] = print) -> dict:
    root, kb = source_dir(), kb_dir()
    entries = catalog.build_catalog(scan(root), load_overrides(kb))
    if dry_run:
        _print_catalog(entries, out)
        return dict(Counter(e.decision for e in entries))
    if not _lock.acquire(blocking=False):
        out("A scan is already running.")
        return {"already_running": True}
    try:
        return _run(root, entries, full, out)
    finally:
        _lock.release()


def run_quietly() -> None:
    """For background threads: log instead of print, never raise."""
    try:
        run(out=logger.info)
    except Exception:
        logger.exception("Handouts scan failed")


def _run(root: Path, entries, full: bool, out) -> dict:
    conn = store.connect(db_path())
    changed = unchanged = duplicates = 0
    seen = set()
    for e in entries:
        seen.add(e.path)
        version = "-".join(str(v) for v in e.version if v != "")
        if e.decision != catalog.KEEP:
            doc = store.get_document(conn, e.path)
            if doc is None or doc["status"] != e.decision or doc["superseded_by"] != e.superseded_by:
                store.record_without_text(conn, path=e.path, family=e.family, version=version, sha256=None,
                                          status=e.decision, superseded_by=e.superseded_by)
            continue
        file = root / e.path
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        doc = store.get_document(conn, e.path)
        if doc is not None and doc["sha256"] == sha and not full:
            unchanged += 1
            continue
        text = extract_text(file)
        text_sha = hashlib.sha256(" ".join(text.split()).encode()).hexdigest()
        if (twin := store.find_by_text_sha(conn, text_sha, other_than=e.path)) is not None:
            store.record_without_text(conn, path=e.path, family=e.family, version=version, sha256=sha,
                                      status=catalog.SKIPPED, superseded_by=twin["path"])
            duplicates += 1
            out(f"  identical text, not indexed: {e.path} (same as {twin['path']})")
            continue
        title, doc_date, sections = split(text)
        doc_id = store.replace_document(
            conn, path=e.path, family=e.family, version=version, title=title or Path(e.path).stem,
            doc_date=doc_date, sha256=sha, text_sha=text_sha,
            sections=[(heading, chunk(body)) for heading, body in sections])
        conn.executemany("insert into glossary_auto(abbr, expansion, document_id) values (?,?,?)",
                         [(a, x, doc_id) for a, x in harvest_abbreviations(text)])
        changed += 1
        out(f"  indexed: {e.path}")
        conn.commit()

    for row in conn.execute("select path from documents where source_kind = 'handout' and status = 'KEEP'").fetchall():
        if row["path"] not in seen:
            store.set_status(conn, row["path"], catalog.RETIRED, "removed from the folder")
            out(f"  removed from the folder: {row['path']}")
    conn.commit()

    embedded = _fill_embeddings(conn, out)
    store.set_meta(conn, "last_scan", store._now())
    store.set_meta(conn, "index_version", store._now())
    conn.commit()
    summary = {"indexed": changed, "unchanged": unchanged, "identical_text": duplicates, "embedded": embedded,
               **store.counts(conn)}
    conn.close()
    out(f"Scan done: {summary}")
    return summary


def _fill_embeddings(conn, out) -> int:
    pending = store.missing_embeddings(conn)
    done = 0
    for i in range(0, len(pending), EMBED_BATCH):
        batch = pending[i:i + EMBED_BATCH]
        vectors = embed([t for _, t in batch], "document")
        if vectors is None:
            out(f"  LM Studio embeddings unavailable; {len(pending) - done} chunks wait for the next scan")
            break
        store.save_embeddings(conn, [cid for cid, _ in batch], vectors)
        conn.commit()
        done += len(batch)
        out(f"  embedded {done}/{len(pending)} chunks")
    return done


ABBR_AFTER = re.compile(r"((?:[\w’'&-]+[ ]){1,6})\(([A-Z]{2,5})\)")
ABBR_BEFORE = re.compile(r"\b([A-Z]{2,5}) \(([A-Z][\w’' &-]{3,60})\)")


def harvest_abbreviations(text: str) -> set[tuple[str, str]]:
    """'Multi-Frequency transmission (MF)' -> ('MF', 'Multi-Frequency') when the capitalised initials match."""
    found = set()
    for m in ABBR_AFTER.finditer(text):
        words, abbr = m.group(1).split(), m.group(2)
        for n in range(1, len(words) + 1):
            phrase = words[-n:]
            if _initials(phrase) == abbr:
                found.add((abbr, " ".join(phrase)))
                break
    for m in ABBR_BEFORE.finditer(text):
        if _initials(m.group(2).split()) == m.group(1):
            found.add((m.group(1), m.group(2).strip()))
    return found


def _initials(words: list[str]) -> str:
    parts = [p for w in words for p in w.split("-") if p[:1].isupper()]
    return "".join(p[0] for p in parts)


def _print_catalog(entries, out) -> None:
    for decision in (catalog.KEEP, catalog.RETIRED, catalog.SKIPPED, catalog.NEEDS_DECISION):
        group = [e for e in entries if e.decision == decision]
        out(f"\n=== {decision} ({len(group)})")
        for e in group:
            extra = f"  <- {e.superseded_by}" if e.superseded_by else ""
            out(f"  {e.path}" + ("" if decision == catalog.KEEP else f"   [{e.reason}]{extra}"))
