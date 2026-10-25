# ADR-0008: Handouts knowledge base: catalogue, hybrid search, data outside the repository

**Status:** Accepted. **Date:** 2026-10-23. **Trigger:** v1 handouts search (ADR-0003) read no `.doc` file, indexed retired versions next to current ones, and missed questions Daniel actually asks. Plan: `docs/plans/PLAN-handouts-knowledge-base-2610212112.md`.

## Context

The source folder holds 193 files: most handouts as a `.doc` and a `.pdf` of the same version, plus `OLD/` folders, Redline drafts, audio and a zip. `python-docx` cannot read `.doc`, so v1 indexed 100 PDFs only, including superseded versions. macOS `textutil` reads every `.doc`/`.docx` cleanly. LM Studio already serves a nomic embedding model next to Qwen. The repository is public; handout text is confidential teaching material.

## Decision

Build the index in `backend/handouts/`: a catalogue keeps one file per handout family (highest version number; `-Edit`, `-letter`, `-for-PDF` are marks, not versions; `.doc` preferred over a same-version `.pdf`; `OLD/` and Redline skipped; dated names wait for a decision in `catalog_overrides.yaml`); text from `textutil` and `pypdf`; heading-aware sections and 250-400 word chunks; SQLite with FTS5 plus nomic embeddings via LM Studio, fused by reciprocal rank fusion, with glossary expansion of abbreviations. Everything derived from the handouts (index, glossary, notes, eval questions) lives in `HANDOUTS_KB_DIR`, outside the repository. Scans are incremental by file hash and run at backend start and on Rescan.

## Consequences

- LM Studio must have the nomic model loaded for meaning-based search; without it, search falls back to keywords and the next scan fills missing embeddings.
- Handout files whose names break the version pattern need a line in `catalog_overrides.yaml`; the dry run (`python -m handouts ingest --dry-run`) shows them.
- The index is rebuilt, not migrated: a schema change means deleting `kb.sqlite` and scanning again (about 30 seconds).
- `sentence-transformers` (and torch) and `python-docx` leave the dependencies; `PyYAML` is declared because Daniel edits YAML files the code reads.

- Added with story 4 (2026-10-24): Daniel's teacher notes are Markdown files in `HANDOUTS_KB_DIR/notes`, a trusted source layer: cited as "Teacher note", ranked above equally matching handout passages, and followed by answers where the handouts disagree. They cost nothing to keep in sync: a scan or a save re-indexes them.

## Alternatives rejected

- Keep sentence-transformers: a heavy dependency for a weaker model, when LM Studio already serves an embedder.
- A vector database: one user and about 2,400 chunks fit in SQLite and memory.
- A file watcher: a scan at startup plus a Rescan button covers one person adding handouts occasionally.
- A hosted model or embedding API: handout content would leave the machine.
