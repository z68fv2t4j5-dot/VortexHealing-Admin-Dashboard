"""SQLite store for the handouts index: documents, sections, chunks, FTS5 and embeddings.

The database lives in kb_dir() (outside the repository) and can always be rebuilt
from the source folder, so there are no migrations: a schema change means a rebuild.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

SCHEMA = """
create table if not exists documents(
    id integer primary key, path text unique not null, family text, version text,
    title text, doc_date text, sha256 text, text_sha text,
    status text not null, superseded_by text, source_kind text not null default 'handout', indexed_at text);
create table if not exists sections(
    id integer primary key, document_id integer not null references documents(id) on delete cascade,
    ord integer, heading_path text);
create table if not exists chunks(
    id integer primary key, section_id integer not null references sections(id) on delete cascade,
    document_id integer not null references documents(id) on delete cascade,
    ord integer, text text not null, embedding blob);
create virtual table if not exists chunks_fts using fts5(text, heading, title, tokenize='porter unicode61');
create table if not exists glossary_auto(abbr text, expansion text, document_id integer references documents(id) on delete cascade);
create table if not exists eval_runs(id integer primary key, ran_at text, hits integer, total integer);
create table if not exists meta(key text primary key, value text);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    # WAL lets the page search while a background scan writes.
    conn.execute("pragma journal_mode = wal")
    conn.executescript(SCHEMA)
    return conn


def get_document(conn, path: str) -> Optional[sqlite3.Row]:
    return conn.execute("select * from documents where path = ?", (path,)).fetchone()


def find_by_text_sha(conn, text_sha: str, other_than: str) -> Optional[sqlite3.Row]:
    return conn.execute("select * from documents where text_sha = ? and path != ? and status = 'KEEP'",
                        (text_sha, other_than)).fetchone()


def delete_document(conn, path: str) -> None:
    doc = get_document(conn, path)
    if doc:
        conn.execute("delete from chunks_fts where rowid in (select id from chunks where document_id = ?)", (doc["id"],))
        conn.execute("delete from documents where id = ?", (doc["id"],))


def replace_document(conn, *, path, family, version, title, doc_date, sha256, text_sha,
                     sections: list[tuple[tuple[str, ...], list[str]]], source_kind="handout") -> int:
    """Insert a document with its sections and chunks, replacing any earlier copy of that path."""
    delete_document(conn, path)
    cur = conn.execute(
        "insert into documents(path, family, version, title, doc_date, sha256, text_sha, status, source_kind, indexed_at)"
        " values (?,?,?,?,?,?,?, 'KEEP', ?, ?)",
        (path, family, version, title, doc_date, sha256, text_sha, source_kind, _now()))
    doc_id = cur.lastrowid
    for s_ord, (heading_path, chunks) in enumerate(sections):
        heading = " > ".join(heading_path)
        sec_id = conn.execute("insert into sections(document_id, ord, heading_path) values (?,?,?)",
                              (doc_id, s_ord, heading)).lastrowid
        for c_ord, text in enumerate(chunks):
            chunk_id = conn.execute("insert into chunks(section_id, document_id, ord, text) values (?,?,?,?)",
                                    (sec_id, doc_id, c_ord, text)).lastrowid
            conn.execute("insert into chunks_fts(rowid, text, heading, title) values (?,?,?,?)",
                         (chunk_id, text, heading, title))
    return doc_id


def record_without_text(conn, *, path, family, version, sha256, status, superseded_by=None) -> None:
    """Keep a row for a file that is not indexed (retired, skipped, identical text) so status can explain it."""
    delete_document(conn, path)
    conn.execute("insert into documents(path, family, version, sha256, status, superseded_by, indexed_at)"
                 " values (?,?,?,?,?,?,?)", (path, family, version, sha256, status, superseded_by, _now()))


def set_status(conn, path: str, status: str, superseded_by: Optional[str] = None) -> None:
    conn.execute("update documents set status = ?, superseded_by = ? where path = ?", (status, superseded_by, path))


def missing_embeddings(conn) -> list[tuple[int, str]]:
    rows = conn.execute("select c.id, c.text from chunks c join documents d on d.id = c.document_id"
                        " where c.embedding is null and d.status = 'KEEP' order by c.id").fetchall()
    return [(r["id"], r["text"]) for r in rows]


def save_embeddings(conn, ids: list[int], vectors: np.ndarray) -> None:
    conn.executemany("update chunks set embedding = ? where id = ?",
                     [(v.astype(np.float32).tobytes(), i) for i, v in zip(ids, vectors)])


def load_embeddings(conn) -> tuple[list[int], Optional[np.ndarray]]:
    rows = conn.execute("select c.id, c.embedding from chunks c join documents d on d.id = c.document_id"
                        " where c.embedding is not null and d.status = 'KEEP'").fetchall()
    if not rows:
        return [], None
    return [r["id"] for r in rows], np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])


def get_meta(conn, key: str) -> Optional[str]:
    row = conn.execute("select value from meta where key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn, key: str, value: str) -> None:
    conn.execute("insert into meta(key, value) values (?, ?) on conflict(key) do update set value = excluded.value",
                 (key, value))


def counts(conn) -> dict:
    one = lambda sql: conn.execute(sql).fetchone()[0]
    return {
        "documents": one("select count(*) from documents where status = 'KEEP' and source_kind = 'handout'"),
        "retired": one("select count(*) from documents where status = 'RETIRED'"),
        "sections": one("select count(*) from sections s join documents d on d.id = s.document_id where d.status = 'KEEP'"),
        "chunks": one("select count(*) from chunks c join documents d on d.id = c.document_id where d.status = 'KEEP'"),
        "chunks_without_embeddings": one("select count(*) from chunks c join documents d on d.id = c.document_id"
                                         " where d.status = 'KEEP' and c.embedding is null"),
        "notes": one("select count(*) from documents where status = 'KEEP' and source_kind = 'note'"),
    }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
