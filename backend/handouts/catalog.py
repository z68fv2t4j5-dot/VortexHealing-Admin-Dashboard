"""Decide which handout files count: one current file per handout family.

Pure: takes relative paths, returns a decision per path. Rules are in the plan's
"Catalogue rules" section. Highest version number wins; `-Edit`, `-letter` and
`-for-PDF` are format or edit marks, not versions or separate handouts.
"""
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Optional

KEEP, RETIRED, SKIPPED, NEEDS_DECISION = "KEEP", "RETIRED", "SKIPPED", "NEEDS_DECISION"

TEXT_TYPES = {".doc": 0, ".docx": 0, ".pdf": 1}  # lower rank is preferred on a tie
FORMAT_SUFFIXES = ("-edit", "-letter", "-for-pdf")
VERSION = re.compile(r"-?(\d+)(?:-?([a-z]))?$")
MONTHS = {"jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
          "january", "february", "march", "april", "june", "july", "august", "september",
          "october", "november", "december"}

# Daniel, 2026-10-21: the 2026 manual is current. Overrides map a file name to KEEP, SKIP or RETIRE.
DEFAULT_OVERRIDES = {
    "2026-Foundational-Manual-(Oct 1)-Letter.pdf": "KEEP",
    "Foundational-Manual-2022-Feb-26.pdf": "RETIRE",
    "Foundational-Training-Manual-2022-Nov.pdf": "RETIRE",
}


@dataclass
class Entry:
    path: str
    family: str
    version: tuple
    decision: str
    reason: str
    superseded_by: Optional[str] = None


def family_and_version(name: str) -> tuple[str, tuple, bool]:
    """'MI-Review-20-Edit.doc' -> ('mi-review', (20, ''), had_format_suffix)."""
    stem = PurePosixPath(name).stem.lower()
    marked = False
    stripped = True
    while stripped:
        stripped = False
        for suffix in FORMAT_SUFFIXES:
            if stem.endswith(suffix):
                stem, marked, stripped = stem[: -len(suffix)], True, True
    m = VERSION.search(stem)
    if not m or m.start() == 0:
        return stem, (), marked
    return stem[: m.start()], (int(m.group(1)), m.group(2) or ""), marked


def _skip_reason(path: PurePosixPath) -> Optional[str]:
    if any(part.lower() == "old" for part in path.parts[:-1]):
        return "in an OLD folder"
    if "redline" in path.name.lower():
        return "Redline draft"
    if path.name.startswith("~$") or path.name.startswith("."):
        return "system or lock file"
    if path.suffix.lower() not in TEXT_TYPES:
        return f"unsupported type {path.suffix or '(none)'}"
    return None


def _is_dated(family: str) -> bool:
    return bool(MONTHS & set(re.findall(r"[a-z]+", family)))


def build_catalog(paths: list[str], overrides: Optional[dict] = None) -> list[Entry]:
    rules = {**DEFAULT_OVERRIDES, **(overrides or {})}
    entries: dict[str, Entry] = {}
    families: dict[str, list[tuple[Entry, bool]]] = {}

    for raw in paths:
        path = PurePosixPath(raw)
        family, version, marked = family_and_version(path.name)
        entry = Entry(raw, family, version, KEEP, "current version")
        entries[raw] = entry
        rule = rules.get(path.name, "").upper()
        if rule == "SKIP":
            entry.decision, entry.reason = SKIPPED, "override"
        elif rule == "RETIRE":
            entry.decision, entry.reason = RETIRED, "override"
        elif rule == "KEEP":
            entry.reason = "override"
        elif (reason := _skip_reason(path)) is not None:
            entry.decision, entry.reason = SKIPPED, reason
        else:
            families.setdefault(family, []).append((entry, marked))

    for family, members in families.items():
        if _is_dated(family):
            for entry, _ in members:
                entry.decision, entry.reason = NEEDS_DECISION, "dated name; set KEEP/SKIP/RETIRE in catalog_overrides"
            continue
        # Best first: highest version, then no -letter/-for-PDF mark, then .doc/.docx over .pdf, then path.
        members.sort(key=lambda m: (_neg(m[0].version), m[1], TEXT_TYPES[PurePosixPath(m[0].path).suffix.lower()], m[0].path))
        winner = members[0][0]
        for entry, _ in members[1:]:
            entry.superseded_by = winner.path
            if entry.version == winner.version:
                entry.decision, entry.reason = SKIPPED, "same version as the kept file"
            else:
                entry.decision, entry.reason = RETIRED, "older version"

    return [entries[p] for p in paths]


def _neg(version: tuple) -> tuple:
    """Sort key putting the highest version first; an unversioned file sorts last."""
    if not version:
        return (1, 0, "")
    number, letter = version
    return (0, -number, "".join(chr(255 - ord(c)) for c in letter) or "\xff")
