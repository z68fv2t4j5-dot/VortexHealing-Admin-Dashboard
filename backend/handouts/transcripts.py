"""Class transcripts: spoken-class and healing-session Markdown files from TRANSCRIPTS_DIR.

Indexed like teacher notes (same store, source_kind='transcript') but kept out of the
default search and out of answers: transcripts are unedited speech and would otherwise
swamp the 74 tuned handouts. Folders starting with '_' and the zoom-import folder hold
private or tooling files and are never indexed. The files themselves are confidential
and stay outside the repository, like everything in HANDOUTS_KB_DIR.
"""
import hashlib
import re
from pathlib import Path
from typing import Callable, Optional

from handouts import store, transcripts_dir
from handouts.sections import chunk

DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")
SKIP_DIRS = {"zoom-import"}


def _files(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root)
        parts = rel.parts
        if any(p.startswith("_") or p in SKIP_DIRS for p in parts):
            continue
        found[f"transcripts/{rel.as_posix()}"] = f
    return found


def file_path(rel: str) -> Optional[Path]:
    """Resolves transcripts/<rel> to a real file inside the folder, or None."""
    root = transcripts_dir()
    if root is None:
        return None
    root = root.resolve()
    path = (root / rel).resolve()
    if root not in path.parents or not path.exists():
        return None
    return path


def index(conn, out: Callable[[str], None] = print) -> int:
    """Indexes new or changed transcripts and drops deleted ones; returns how many changed."""
    root = transcripts_dir()
    files = _files(root) if root and root.exists() else {}
    changed = 0
    for path, f in files.items():
        raw = f.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        doc = store.get_document(conn, path)
        if doc is not None and doc["sha256"] == sha:
            continue
        body = raw.decode("utf-8", errors="replace").strip()
        if not body:
            continue
        title = f.stem
        m = DATE_PREFIX.match(f.name)
        family = f.relative_to(root).parts[0] if len(f.relative_to(root).parts) > 1 else "transcripts"
        store.replace_document(conn, path=path, family=f"transcript:{family}", version="", title=title,
                               doc_date=m.group(1) if m else None, sha256=sha,
                               text_sha=hashlib.sha256(body.encode()).hexdigest(),
                               sections=[((title,), body, chunk(body))], source_kind="transcript")
        changed += 1
        out(f"  transcript indexed: {path}")
    for row in conn.execute("select path from documents where source_kind = 'transcript'").fetchall():
        if row["path"] not in files:
            store.delete_document(conn, row["path"])
            changed += 1
            out(f"  transcript removed: {row['path']}")
    conn.commit()
    return changed
