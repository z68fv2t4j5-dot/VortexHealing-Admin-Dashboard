"""Hybrid search: glossary expansion -> FTS5 BM25 + vector similarity -> reciprocal rank fusion.

Falls back to keyword search alone when embeddings or LM Studio are unavailable.
"""
import re
import sqlite3
from typing import Optional

import numpy as np
import yaml

from handouts import kb_dir, store
from handouts.embed import embed

CANDIDATES = 40
RRF_K = 60
PER_DOCUMENT = 3
STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "can", "do", "does", "for", "from", "get", "how",
             "i", "in", "is", "it", "of", "on", "or", "should", "that", "the", "this", "to", "used", "what",
             "whats", "when", "where", "which", "who", "why", "with", "you", "your"}

_vectors: dict = {}  # cache of (index_version) -> (chunk ids, matrix)


def search(query: str, limit: int = 10, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    from handouts.ingest import db_path

    own = conn is None
    conn = conn or store.connect(db_path())
    try:
        expanded = expand(query, glossary(conn))
        ranked = [_keyword(conn, expanded)]
        if (semantic := _semantic(conn, expanded)) is not None:
            ranked.append(semantic)
        fused = fuse(ranked)
        return _passages(conn, sorted(fused, key=fused.get, reverse=True), fused, limit)
    finally:
        if own:
            conn.close()


def fuse(rankings: list[list[int]]) -> dict[int, float]:
    """Reciprocal rank fusion: an item ranked well in both lists beats one ranked first in only one."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            fused[item] = fused.get(item, 0.0) + 1.0 / (RRF_K + rank + 1)
    return fused


def glossary(conn) -> dict[str, list[str]]:
    """Abbreviation -> expansions. Daniel's glossary.yaml wins over what the scan harvested."""
    found: dict[str, list[str]] = {}
    for row in conn.execute("select abbr, expansion, count(*) n from glossary_auto group by abbr, expansion order by n desc"):
        found.setdefault(row["abbr"], [row["expansion"]])
    return {**found, **daniel_glossary()}


def daniel_glossary() -> dict[str, list[str]]:
    """Only the abbreviations Daniel confirmed in glossary.yaml."""
    f = kb_dir() / "glossary.yaml"
    if not f.exists():
        return {}
    found = {}
    for abbr, value in (yaml.safe_load(f.read_text()) or {}).items():
        values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        # A bare `[?]` parses as a mapping, not text: keep only plain-text expansions.
        values = [v for v in values if isinstance(v, str) and v.strip()]
        if values and str(abbr).isupper():
            found[str(abbr)] = values
    return found


def expand(query: str, gloss: dict[str, list[str]]) -> str:
    extra = [x for token in re.findall(r"[A-Za-z]+", query) for x in gloss.get(token.upper(), [])
             if len(token) >= 2 and "?" not in x]
    return " ".join([query, *extra])


def _keyword(conn, query: str) -> list[int]:
    terms = [t for t in re.findall(r"\w+", query.lower()) if t not in STOPWORDS and len(t) > 1]
    if not terms:
        return []
    match = " OR ".join(f'"{t}"' for t in dict.fromkeys(terms))
    rows = conn.execute(
        "select f.rowid from chunks_fts f join chunks c on c.id = f.rowid join documents d on d.id = c.document_id"
        " where chunks_fts match ? and d.status = 'KEEP' order by bm25(chunks_fts, 1.0, 2.0, 1.5) limit ?",
        (match, CANDIDATES)).fetchall()
    return [r[0] for r in rows]


def _semantic(conn, query: str) -> Optional[list[int]]:
    version = store.get_meta(conn, "index_version")
    if _vectors.get("version") != version:
        _vectors.update(version=version, data=store.load_embeddings(conn))
    ids, matrix = _vectors["data"]
    if matrix is None:
        return None
    q = embed([query], "query")
    if q is None:
        return None
    scores = matrix @ q[0]
    top = np.argsort(-scores)[:CANDIDATES]
    return [ids[i] for i in top]


def _passages(conn, chunk_ids: list[int], scores: dict[int, float], limit: int) -> list[dict]:
    out, per_doc = [], {}
    for cid in chunk_ids:
        row = conn.execute(
            "select c.id, c.text, s.heading_path, d.id doc_id, d.title, d.family, d.version, d.path, d.doc_date, d.source_kind"
            " from chunks c join sections s on s.id = c.section_id join documents d on d.id = c.document_id"
            " where c.id = ? and d.status = 'KEEP'", (cid,)).fetchone()
        if row is None or per_doc.get(row["doc_id"], 0) >= PER_DOCUMENT:
            continue
        per_doc[row["doc_id"]] = per_doc.get(row["doc_id"], 0) + 1
        out.append({"chunk_id": row["id"], "text": row["text"], "heading_path": row["heading_path"],
                    "document_id": row["doc_id"], "title": row["title"], "family": row["family"],
                    "version": row["version"], "path": row["path"], "doc_date": row["doc_date"],
                    "source_kind": row["source_kind"], "score": round(scores[cid], 5)})
        if len(out) >= limit:
            break
    return out
