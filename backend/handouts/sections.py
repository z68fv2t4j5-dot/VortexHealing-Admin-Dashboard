"""Split handout text into a title, a date and headed sections, then into chunks.

Rules are in the plan's "Assumed" and module-table rows: a heading is a short
line (under ~80 characters) without a closing full stop, or a short numbered,
lettered, `Day N:` or `Part N:` line. Chunks are 250-400 words, never cross a
section, and overlap by one sentence.
"""
import re
from typing import Optional

MAX_HEADING_CHARS = 80
MIN_WORDS, MAX_WORDS = 250, 400
MIN_SECTION_WORDS = 15
# Table-of-contents lines: dot leaders, usually with a page number.
TOC_LINE = re.compile(r"(\.{4,}|…{2,})\s*\d*\s*$")

DATE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{4}\b")
# Word-processor debris that textutil leaves in the text ("PAGE  2", "PAGE  ").
DEBRIS = re.compile(r"^\s*PAGE\s*\d*\s*$")
TOP_LEVEL = re.compile(r"^(Part|Section)\s+([0-9]+|[IVX]+)\b", re.I)
MARKED = re.compile(r"^(Day\s+\d+|[0-9]{1,2}[.)]|[A-Za-z][.)]|\([0-9a-z]\))\s")
# A full stop after one of these does not end a sentence.
NO_BREAK_AFTER = re.compile(r"(?:\b(?:approx|e\.g|i\.e|etc|vs|no|Dr|Mr|Mrs|Ms|St)\.|\b[0-9]{1,2}\.|\b[a-zA-Z]\.)$")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"'’”)]?\s+(?=[\"'‘“(]?[A-Z0-9])")


def split(text: str) -> tuple[str, Optional[str], list[tuple[tuple[str, ...], str]]]:
    #  and friends are Word Symbol-font bullets that survive PDF extraction.
    lines = [ln.strip().lstrip("• ").strip() for ln in text.replace("\f", "\n").splitlines()]
    # An indented line is a list item or a continuation, never a heading (MG ending options:
    # short tab-indented items without full stops had each become a "section").
    indented = [bool(re.match(r"[ \t]+\S", raw)) for raw in text.replace("\f", "\n").splitlines()]
    keep = [i for i, ln in enumerate(lines) if not DEBRIS.match(ln)]
    lines, indented = [lines[i] for i in keep], [indented[i] for i in keep]
    title = next((ln for ln in lines if ln), "")
    head = "\n".join(lines[:10])
    doc_date = m.group(0) if (m := DATE.search(head)) else None

    sections: list[tuple[tuple[str, ...], str]] = []
    top: Optional[str] = None
    path: tuple[str, ...] = ()
    body: list[str] = []
    carry = ""  # a section too small to stand alone is folded into the next one

    def flush():
        nonlocal carry
        text = " ".join(" ".join(body).split())
        body.clear()
        if text and len(text.split()) < MIN_SECTION_WORDS:
            carry = " ".join(filter(None, [carry, path[-1] if path else "", text]))
        elif text:
            sections.append((path, " ".join(filter(None, [carry, text]))))
            carry = ""

    prev, prev_heading = "", False
    for i, line in enumerate(lines):
        if not line or line == title or TOC_LINE.search(line) or line == doc_date:
            if not line:
                prev = ""
            continue
        nxt = next((ln for ln in lines[i + 1:] if ln), "")
        # PDFs hard-wrap paragraphs: a short line that continues a sentence, or is
        # continued by a lower-case line, is body text, not a heading.
        starts_block = not prev or prev[-1] in ".!?:" or prev_heading
        if not indented[i] and is_heading(line) and starts_block and not nxt[:1].islower():
            flush()
            label = line.rstrip(":").strip()
            if TOP_LEVEL.match(line):
                top, path = label, (label,)
            else:
                path = (top, label) if top else (label,)
            prev_heading = True
        else:
            body.append(line)
            prev_heading = False
        prev = line
    flush()
    if carry:
        if sections:
            p, t = sections[-1]
            sections[-1] = (p, f"{t} {carry}")
        else:
            sections.append((path, carry))
    return title, doc_date, sections


def is_heading(line: str) -> bool:
    if len(line) > MAX_HEADING_CHARS or not re.search(r"[A-Za-z]{2}", line):
        return False
    if line[-1] in ".,;" or line[0].islower() or DATE.fullmatch(line.strip("() ")):
        return False
    # Every number in it is a list marker or a short label, not a figure in a sentence.
    return bool(TOP_LEVEL.match(line) or MARKED.match(line) or len(line.split()) <= 12)


def sentences(text: str) -> list[str]:
    out, start = [], 0
    for m in SENTENCE_END.finditer(text):
        piece = text[start:m.start()].strip()
        if NO_BREAK_AFTER.search(piece.rstrip("\"'’”)")):
            continue
        out.append(piece)
        start = m.end()
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def chunk(section_text: str) -> list[str]:
    words = lambda s: len(s.split())
    sents: list[str] = []
    for s in sentences(section_text):
        # A sentence longer than a whole chunk is cut into word windows.
        ws = s.split()
        sents += [" ".join(ws[i:i + MAX_WORDS]) for i in range(0, len(ws), MAX_WORDS)] or [s]

    chunks: list[list[str]] = []
    current: list[str] = []
    for s in sents:
        if current and sum(map(words, current)) + words(s) > MAX_WORDS:
            chunks.append(current)
            current = [current[-1]] if words(current[-1]) + words(s) <= MAX_WORDS else []
        current.append(s)
    # A short tail joins the previous chunk when it fits, rather than standing alone.
    if current and chunks and sum(map(words, current)) < MIN_WORDS:
        tail = current[1:] if current[0] == chunks[-1][-1] else current
        if sum(map(words, chunks[-1] + tail)) <= MAX_WORDS:
            chunks[-1] += tail
            current = []
    if current:
        chunks.append(current)
    return [" ".join(c) for c in chunks]
