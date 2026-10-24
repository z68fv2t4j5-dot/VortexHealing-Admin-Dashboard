"""Teacher notes: Daniel's own knowledge, kept as Markdown files in HANDOUTS_KB_DIR/notes.

A note has YAML front matter (topic, entities it is about, the handout it corrects) and a body. Notes are
indexed like handouts but cited as "Teacher note", outrank handout passages of equal relevance, appear on
the cards of the entities they name, and override the handouts in answers where they disagree.
"""
import hashlib
import re
from datetime import date
from pathlib import Path
from typing import Callable, Optional

import yaml

from handouts import kb_dir, store
from handouts.sections import chunk

FILE_NAME = re.compile(r"^[\w-]+\.md$")
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def notes_dir() -> Path:
    return kb_dir() / "notes"


def note_path(name: str) -> Path:
    """A note's file, refusing anything that is not a plain file name in the notes folder."""
    if not FILE_NAME.match(name):
        raise ValueError(f"not a note file name: {name!r}")
    return notes_dir() / name


def parse(text: str) -> dict:
    meta, body = {}, text
    if m := FRONT_MATTER.match(text):
        loaded = yaml.safe_load(m.group(1))
        meta, body = (loaded if isinstance(loaded, dict) else {}), m.group(2)
    entities = meta.get("entities") or []
    return {"topic": str(meta.get("topic") or "").strip(),
            "entities": [str(e).strip() for e in (entities if isinstance(entities, list) else [entities]) if str(e).strip()],
            "corrects": str(meta["corrects"]).strip() if meta.get("corrects") else None,
            "body": body.strip()}


def render(topic: str, body: str, entities: list[str], corrects: Optional[str]) -> str:
    front = yaml.safe_dump({"topic": topic, "entities": entities, "corrects": corrects},
                           sort_keys=False, allow_unicode=True).strip()
    return f"---\n{front}\n---\n\n{body.strip()}\n"


def note_date(name: str) -> Optional[str]:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else None


def list_notes() -> list[dict]:
    if not notes_dir().exists():
        return []
    return [{"file": f.name, "date": note_date(f.name), **parse(f.read_text())}
            for f in sorted(notes_dir().glob("*.md"), reverse=True)]


def save(topic: str, body: str, entities: Optional[list[str]] = None, corrects: Optional[str] = None,
         name: Optional[str] = None) -> str:
    """Writes a new note (name None) or replaces an existing one; returns its file name."""
    if not topic.strip() or not body.strip():
        raise ValueError("a note needs a topic and some text")
    notes_dir().mkdir(parents=True, exist_ok=True)
    if name is None:
        base = f"{date.today():%Y-%m-%d}-{re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')[:50] or 'note'}"
        name, n = f"{base}.md", 2
        while (notes_dir() / name).exists():
            name, n = f"{base}-{n}.md", n + 1
    elif not note_path(name).exists():
        raise FileNotFoundError(name)
    note_path(name).write_text(render(topic.strip(), body, [e.strip() for e in entities or [] if e.strip()],
                                      (corrects or "").strip() or None))
    return name


def delete(name: str) -> None:
    note_path(name).unlink()


def index(conn, out: Callable[[str], None] = print) -> int:
    """Indexes new or changed note files and drops deleted ones; returns how many changed."""
    files = {f"notes/{f.name}": f for f in notes_dir().glob("*.md")} if notes_dir().exists() else {}
    changed = 0
    for path, f in files.items():
        raw = f.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        doc = store.get_document(conn, path)
        if doc is not None and doc["sha256"] == sha:
            continue
        note = parse(raw.decode("utf-8", errors="replace"))
        if not note["body"]:
            continue
        topic = note["topic"] or f.stem
        store.replace_document(conn, path=path, family=f"note:{f.stem}", version="", title=f"Teacher note: {topic}",
                               doc_date=note_date(f.name), sha256=sha,
                               text_sha=hashlib.sha256(note["body"].encode()).hexdigest(),
                               sections=[((topic,), note["body"], chunk(note["body"]))], source_kind="note")
        changed += 1
        out(f"  note indexed: {f.name}")
    for row in conn.execute("select path from documents where source_kind = 'note'").fetchall():
        if row["path"] not in files:
            store.delete_document(conn, row["path"])
            changed += 1
            out(f"  note removed: {row['path']}")
    conn.commit()
    return changed


def for_entity(conn, name: str) -> list[dict]:
    """Notes that name this entity, or whose topic is it."""
    from handouts.knowledge import norm

    key = norm(name)
    found = []
    for n in list_notes():
        if key in {norm(e) for e in n["entities"]} | {norm(n["topic"])}:
            doc = store.get_document(conn, f"notes/{n['file']}")
            found.append({**n, "document_id": doc["id"] if doc else None})
    return found
