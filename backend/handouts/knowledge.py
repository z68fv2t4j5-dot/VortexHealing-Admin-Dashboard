"""Knowledge map: Qwen reads each section once and records entities and facts, each tied to its section.

Readings are cached by section text hash (extraction_cache); entities and facts are rebuilt from the
cache by apply(), so re-indexing never repeats the overnight run for unchanged text.
"""
import asyncio
import json
import logging
import re
import threading
import time
from typing import Callable, Optional

import httpx
import yaml

from handouts import kb_dir, store
from handouts.retrieve import daniel_glossary

logger = logging.getLogger(__name__)
_lock = threading.Lock()

TYPES = ["tool", "transmission", "class", "conditioning", "structure", "protocol", "being", "place", "concept"]
PREDICATES = {
    "introduced_in": "first received or taught in this class",
    "done_in_class": "how it is done in a given class (put the how in detail: steps, time, depth)",
    "releases": "a tool or technique releases, clears or heals the object",
    "is_source_of": "the subject is a source or cause of the object (conditioning, issues)",
    "is_part_of": "the subject is a part or layer of the object",
    "requires": "the subject needs the object first (a class, tool or condition)",
    "located_in": "where the subject sits (chakra, body, energy system, dimension)",
    "related_to": "any other important relation; say what in detail",
}
LEVELS = ["physical", "emotional", "mental", "karmic", "genetic", "core veil", "energetic", "blueprint",
          "present life", "none"]

SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "type": {"type": "string", "enum": TYPES},
            "aliases": {"type": "array", "items": {"type": "string"}},
            "definition": {"type": "string"}}, "required": ["name", "type", "definition"]}},
        "facts": {"type": "array", "items": {"type": "object", "properties": {
            "subject": {"type": "string"}, "predicate": {"type": "string", "enum": list(PREDICATES)},
            "object": {"type": "string"}, "detail": {"type": "string"},
            "level": {"type": "string", "enum": LEVELS}}, "required": ["subject", "predicate", "object"]}},
    },
    "required": ["entities", "facts"],
}

PROMPT = """You build a knowledge map of VortexHealing class handouts. From the section given, list:
- entities: the VortexHealing tools, transmissions, classes, kinds of conditioning, energetic structures,
  protocols, beings and places it explains. Use the name as the handout writes it. definition: at most two
  sentences, from this text only. Skip ordinary words and things only mentioned in passing.
- facts: relations stated in this text, one per fact. Predicates:
{predicates}
  detail: at most 20 words (steps, timings, percentages, conditions), or "" if the text gives none. level: the
  kind of conditioning involved, or "none".
{klass}
Only record what this text says: at most 15 entities and 20 facts, the most important first. If it explains
nothing worth mapping, return empty lists.
Abbreviations: {glossary}.
Reply with JSON only, in exactly this shape (without an example, the model returns empty lists):
{{"entities":[{{"name":"...","type":"tool","aliases":[],"definition":"..."}}],"facts":[{{"subject":"...","predicate":"introduced_in","object":"...","detail":"...","level":"none"}}]}}"""


def handout_classes() -> dict[str, Optional[str]]:
    f = kb_dir() / "handout_classes.yaml"
    return (yaml.safe_load(f.read_text()) or {}) if f.exists() else {}


def norm(name: str) -> str:
    """Comparable form of a name: lower case, no apostrophes or punctuation, no leading "the"."""
    name = re.sub(r"[’'`]", "", name.lower())
    name = re.sub(r"[^a-z0-9&]+", " ", name).strip()
    return re.sub(r"^the ", "", name)


def known_classes() -> dict[str, str]:
    """norm -> display name, for every class on the flowchart or named in handout_classes.yaml."""
    from app.class_rules import CLASSES

    names = list(CLASSES) + [c for c in handout_classes().values() if c]
    return {norm(n): n for n in names}


def canonical_class(name: str, classes: dict[str, str], gloss: dict[str, str]) -> Optional[str]:
    """'Multi-Frequency class' or 'MF' -> 'Multi-Frequency'; None when it is not a known class."""
    key = re.sub(r"\b(class|classes|training|course)$", "", norm(name)).strip()
    key = gloss.get(key, key)
    if key in classes:
        return classes[key]
    # "Core Veil" names the class "Core Veil & Awakening to Being Awareness" when only one class starts so.
    starts = [c for c in classes if c.startswith(key + " ")] if len(key) >= 4 else []
    return classes[starts[0]] if len(starts) == 1 else None


def _prompt(klass: Optional[str]) -> str:
    gloss = "; ".join(f"{a} = {' / '.join(v)}" for a, v in daniel_glossary().items())
    where = (f"This handout belongs to the class {klass}: when it says \"this class\" or \"you receive\", "
             f"the class is {klass}." if klass else "This handout is not tied to one class.")
    preds = "\n".join(f"  {p}: {d}" for p, d in PREDICATES.items())
    return PROMPT.format(predicates=preds, klass=where, glossary=gloss or "none")


async def extract(text: str, title: str, heading: str, klass: Optional[str]) -> dict:
    from app.core.config import settings

    body = {"model": settings.QWEN_MODEL, "temperature": 0, "max_tokens": 6000, "reasoning_effort": "none",
            "response_format": {"type": "json_schema", "json_schema": {"name": "map", "strict": False, "schema": SCHEMA}},
            "messages": [{"role": "system", "content": _prompt(klass)},
                         {"role": "user", "content": f"Handout: {title}\nSection: {heading or 'opening'}\n\n{text}"}]}
    async with httpx.AsyncClient(timeout=600) as client:
        r = await client.post(f"{settings.LM_STUDIO_URL}/chat/completions", json=body)
        r.raise_for_status()
        result = json.loads(r.json()["choices"][0]["message"]["content"])
    return {"entities": [e for e in result.get("entities", []) if isinstance(e, dict) and e.get("name")],
            "facts": [f for f in result.get("facts", []) if isinstance(f, dict) and f.get("subject") and f.get("object")]}


def model_name() -> str:
    from app.core.config import settings

    return settings.QWEN_MODEL


def pending(conn) -> list:
    return conn.execute(
        "select s.id, s.text, s.text_sha, s.heading_path, d.title, d.family from sections s"
        " join documents d on d.id = s.document_id"
        " where d.status = 'KEEP' and s.text is not null and length(s.text) > 0"
        " and not exists (select 1 from extraction_cache c where c.text_sha = s.text_sha and c.model = ?)"
        " group by s.text_sha order by d.path, s.ord", (model_name(),)).fetchall()


HEARTBEAT_SECONDS = 180


def is_running(conn=None) -> bool:
    """True while a run in this process holds the lock, or another process (the CLI) has written a
    heartbeat in the last few minutes."""
    if _lock.locked():
        return True
    beat = store.get_meta(conn, "knowledge_heartbeat") if conn is not None else None
    return beat is not None and time.time() - float(beat) < HEARTBEAT_SECONDS


def run(limit: Optional[int] = None, concurrency: int = 3, out: Callable[[str], None] = print) -> dict:
    """Reads every section not yet in the cache, then rebuilds entities and facts. Resumable."""
    from handouts.ingest import db_path

    if not _lock.acquire(blocking=False):
        out("Knowledge extraction is already running.")
        return {"already_running": True}
    try:
        conn = store.connect(db_path())
        todo = pending(conn)[:limit] if limit else pending(conn)
        classes = handout_classes()
        out(f"{len(todo)} sections to read (concurrency {concurrency}).")
        store.set_meta(conn, "knowledge_heartbeat", str(time.time()))
        conn.commit()
        done, failed, start = 0, 0, time.time()

        async def work():
            nonlocal done, failed
            gate = asyncio.Semaphore(concurrency)

            async def one(row):
                nonlocal done, failed
                async with gate:
                    try:
                        result = await extract(row["text"], row["title"], row["heading_path"], classes.get(row["family"]))
                    except (httpx.HTTPError, KeyError, ValueError) as e:
                        failed += 1
                        out(f"  skipped section {row['id']} ({type(e).__name__}); it will be retried next run")
                        return
                conn.execute("insert or replace into extraction_cache(text_sha, model, result, done_at) values (?,?,?,?)",
                             (row["text_sha"], model_name(), json.dumps(result), store._now()))
                conn.commit()
                done += 1
                if done % 10 == 0 or done == len(todo):
                    store.set_meta(conn, "knowledge_heartbeat", str(time.time()))
                    conn.commit()
                    rate = (time.time() - start) / done
                    out(f"  {done}/{len(todo)} read, about {rate * (len(todo) - done) / 60:.0f} min left")

            await asyncio.gather(*(one(r) for r in todo))

        asyncio.run(work())
        summary = {"read": done, "failed": failed, **apply(conn)}
        conn.execute("delete from meta where key = 'knowledge_heartbeat'")
        conn.commit()
        conn.close()
        out(f"Knowledge map: {summary}")
        return summary
    finally:
        _lock.release()


def run_quietly(**kwargs) -> None:
    try:
        run(out=logger.info, **kwargs)
    except Exception:
        logger.exception("Knowledge extraction failed")


def apply(conn) -> dict:
    """Rebuilds entities and facts from the cache for every current section."""
    conn.execute("delete from facts")
    conn.execute("delete from entity_definitions")
    conn.execute("delete from entities")
    gloss = {norm(a): v[0] for a, v in daniel_glossary().items() if v}
    aliases = {a: norm(v) for a, v in gloss.items()}
    full_names = {norm(v): v for v in gloss.values()}
    classes = known_classes()
    ids: dict[str, int] = {}
    types: dict[int, dict[str, int]] = {}
    spellings: dict[int, dict[str, int]] = {}

    def entity(name: str, kind: Optional[str] = None) -> Optional[int]:
        key = aliases.get(norm(name), norm(name))
        if len(key) < 2:
            return None
        if key not in ids:
            ids[key] = conn.execute("insert into entities(name, norm, type, aliases) values (?,?,?,?)",
                                    (name.strip(), key, kind, "[]")).lastrowid
        if kind:
            counts = types.setdefault(ids[key], {})
            counts[kind] = counts.get(kind, 0) + 1
        if norm(name) == key:  # an abbreviation is not a spelling of the full name
            seen = spellings.setdefault(ids[key], {})
            seen[name.strip()] = seen.get(name.strip(), 0) + 1
        return ids[key]

    rows = conn.execute(
        "select s.id, c.result from sections s join documents d on d.id = s.document_id"
        " join extraction_cache c on c.text_sha = s.text_sha and c.model = ? where d.status = 'KEEP'",
        (model_name(),)).fetchall()
    alias_rows: dict[int, set] = {}
    for row in rows:
        result = json.loads(row["result"])
        for e in result.get("entities", []):
            kind = e.get("type")
            if kind == "class":
                klass = canonical_class(e["name"], classes, aliases)
                e = {**e, "name": klass} if klass else e
                kind = "class" if klass else None
            eid = entity(e["name"], kind)
            if eid is None:
                continue
            for a in e.get("aliases") or []:
                if norm(a) and norm(a) != norm(e["name"]):
                    alias_rows.setdefault(eid, set()).add(a.strip())
                    aliases.setdefault(norm(a), next(k for k, v in ids.items() if v == eid))
            if e.get("definition"):
                conn.execute("insert into entity_definitions(entity_id, definition, section_id) values (?,?,?)",
                             (eid, e["definition"].strip(), row["id"]))
        for f in result.get("facts", []):
            if f.get("predicate") not in PREDICATES:
                continue
            subject = entity(f["subject"])
            target_name, target_kind = f["object"], None
            if f["predicate"] in ("introduced_in", "done_in_class"):
                klass = canonical_class(f["object"], classes, aliases)
                target_name, target_kind = (klass, "class") if klass else (f["object"], None)
            target = entity(target_name, target_kind)
            if subject is None:
                continue
            conn.execute("insert into facts(subject_id, predicate, object_id, object_text, detail, level, section_id)"
                         " values (?,?,?,?,?,?,?)",
                         (subject, f["predicate"], target, target_name.strip(), (f.get("detail") or "").strip(),
                          None if f.get("level") in (None, "none") else f["level"], row["id"]))
    for eid, counts in types.items():
        conn.execute("update entities set type = ? where id = ?", (max(counts, key=counts.get), eid))
    # A name that is a class on the flowchart is the class, even where the transmission shares its name (Jewel, MF).
    for key, eid in ids.items():
        if key in classes:
            conn.execute("update entities set type = 'class' where id = ?", (eid,))
    # Display name: Daniel's glossary form, else the commonest capitalised spelling without a leading "the".
    for key, eid in ids.items():
        seen = spellings.get(eid, {})
        best = full_names.get(key) or (max(seen, key=lambda n: (n[:1].isupper(), not n.lower().startswith("the "), seen[n]))
                                       if seen else None)
        if best:
            conn.execute("update entities set name = ? where id = ?", (best, eid))
    for eid, names in alias_rows.items():
        conn.execute("update entities set aliases = ? where id = ?", (json.dumps(sorted(names)), eid))
    conn.commit()
    one = lambda sql: conn.execute(sql).fetchone()[0]
    return {"entities": one("select count(*) from entities"), "facts": one("select count(*) from facts")}


def find_entities(conn, text: str, limit: int = 2) -> list[int]:
    """Entities named in the text (longest names first), that have something to show."""
    q = f" {norm(text)} "
    expansions = {norm(a): norm(v[0]) for a, v in daniel_glossary().items() if v}
    q = " ".join(expansions.get(w, w) for w in q.split())
    q = f" {q} "
    found = []
    rows = conn.execute("select e.id, e.norm, e.aliases, (select count(*) from facts f where f.subject_id = e.id) n"
                        " from entities e where e.type != 'class' or n > 0").fetchall()
    names = [(r["norm"], r["id"], r["n"]) for r in rows]
    names += [(norm(a), r["id"], r["n"]) for r in rows for a in json.loads(r["aliases"] or "[]")]
    for name, eid, n in sorted(names, key=lambda x: (-len(x[0]), -x[2])):
        if n and len(name) >= 4 and f" {name} " in q and eid not in found:
            found.append(eid)
            q = q.replace(f" {name} ", " ")
        if len(found) >= limit:
            break
    return found


def card(conn, entity_id: int) -> Optional[dict]:
    e = conn.execute("select * from entities where id = ?", (entity_id,)).fetchone()
    if e is None:
        return None

    def source(section_id):
        s = conn.execute("select s.id, s.heading_path, d.id doc_id, d.title, d.family from sections s"
                         " join documents d on d.id = s.document_id where s.id = ?", (section_id,)).fetchone()
        return {"section_id": s["id"], "document_id": s["doc_id"], "title": s["title"], "heading_path": s["heading_path"],
                "class": handout_classes().get(s["family"])}

    facts = []
    for f in conn.execute("select f.*, o.name object_name, o.type object_type from facts f"
                          " left join entities o on o.id = f.object_id where f.subject_id = ? order by f.predicate", (entity_id,)):
        facts.append({"predicate": f["predicate"], "object": f["object_name"] or f["object_text"],
                      "object_type": f["object_type"],
                      "object_id": f["object_id"], "detail": f["detail"], "level": f["level"],
                      "source": source(f["section_id"])})
    incoming = []
    for f in conn.execute("select f.*, s.name subject_name from facts f join entities s on s.id = f.subject_id"
                          " where f.object_id = ? order by f.predicate limit 40", (entity_id,)):
        incoming.append({"predicate": f["predicate"], "subject": f["subject_name"], "subject_id": f["subject_id"],
                         "detail": f["detail"], "source": source(f["section_id"])})
    definitions = [{"text": d["definition"], "source": source(d["section_id"])}
                   for d in conn.execute("select * from entity_definitions where entity_id = ?", (entity_id,))]
    # Only real classes: Qwen sometimes names a tool or a place as where something is introduced.
    introduced = sorted({f["object"] for f in facts if f["predicate"] == "introduced_in" and f["object_type"] == "class"})
    # Prefer the definition from the class that introduces it.
    definitions.sort(key=lambda d: (d["source"]["class"] not in introduced, len(d["text"])))
    return {"id": e["id"], "name": e["name"], "type": e["type"], "aliases": json.loads(e["aliases"] or "[]"),
            "introduced_in": introduced, "definitions": definitions[:3], "facts": facts, "incoming": incoming}


def browse(conn, kind: Optional[str] = None, query: str = "", limit: int = 300) -> list[dict]:
    sql = ("select e.id, e.name, e.type, (select count(*) from facts f where f.subject_id = e.id or f.object_id = e.id) n"
           " from entities e where 1=1")
    args: list = []
    if kind:
        sql += " and e.type = ?"
        args.append(kind)
    if query:
        sql += " and e.norm like ?"
        args.append(f"%{norm(query)}%")
    sql += " order by n desc, e.name limit ?"
    args.append(limit)
    return [dict(r) for r in conn.execute(sql, args)]
