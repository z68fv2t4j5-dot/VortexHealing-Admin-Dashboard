# PLAN: class transcripts in the handouts knowledge base

Status: in progress
Branch: feat/transcripts-kb

## Why (PM stance)

Daniel has 600+ class and healing-session transcripts as Markdown in a local folder
(MacWhisper exports of Ric's/Anthony's/Lorraine's classes; his own Zoom sessions).
He wants them searchable from the dashboard's Handouts page. Transcripts are spoken,
unedited and confidential (student names), so they must not change the tuned handout
answers (21/21 on his eval) and must never enter the repository.

Acceptance criteria:
1. With `TRANSCRIPTS_DIR` set, a scan indexes every transcript `.md` (folders starting
   with `_` and the `zoom-import` folder skipped) as `source_kind='transcript'`.
2. `/api/handouts/status` reports a transcripts count; the page shows it.
3. A "Search in" selector on the Handouts page: default Handouts + notes (behaviour
   unchanged — the eval stays 21/21); "Transcripts" or "Everything" includes them.
4. A transcript passage shows its title, folder (teacher) and date, and links to the
   file via `/api/handouts/file/{id}`.
5. Answers (ask mode) are unchanged in this story: they still draw on handouts and
   notes only. Transcript-aware answers are a later story.
6. Without `TRANSCRIPTS_DIR`, everything behaves exactly as today.

## How (ponytail stance)

Copy the teacher-notes pattern (second corpus in the same store) — no new tables, no
new index, no new dependencies:
- `Settings.TRANSCRIPTS_DIR: Optional[str]` + `.env.example` placeholder; `transcripts_dir()`
  helper beside `source_dir()`.
- New `backend/handouts/transcripts.py` mirroring `notes.py.index()`: sha-skip, one
  section per file, `chunk()` for passages, path `transcripts/<relpath>`, family = top
  folder, doc_date = leading `YYYY-MM-DD` in the file name, title = file stem.
- `ingest._run()` calls it after notes (embeddings fill handles the rest); `store.counts()`
  gains `transcripts`.
- `retrieve.search(..., kinds)` filters: keyword SQL gets `d.source_kind in (...)`;
  `_passages` drops non-matching rows from the semantic ranking. Default kinds =
  handout + note (today's behaviour).
- `HandoutsQuery.sources` passes through `/handouts/query` and `/query/stream` for
  search mode only.
- `/handouts/file/{id}`: a `transcripts/` branch like the `notes/` one, traversal-guarded.
- `Handouts.tsx`: source selector (Handouts / Transcripts / Everything), transcript
  passage styling + label, transcripts count in the status line.

First scan after enabling will embed ~15k new chunks via LM Studio (minutes, one-off).

## Tests (named before code)

`backend/tests/test_handouts_transcripts.py`, invented text only (ADR-0008):
- indexes invented transcript files from a tmp dir; counts appear; re-index skips unchanged
- skips `_private/` and `zoom-import/` folders
- `search(kinds={'transcript'})` finds transcript text; default search does not
- file endpoint serves a transcript and 404s a traversal path
- unset `TRANSCRIPTS_DIR` leaves counts at zero and search unchanged
Red witnessed by running the suite before wiring `ingest._run`.

## Surface:

backend/app/core/config.py
backend/.env.example
backend/handouts/__init__.py
backend/handouts/transcripts.py
backend/handouts/ingest.py
backend/handouts/store.py
backend/handouts/retrieve.py
backend/app/api/handouts.py
backend/tests/test_handouts_transcripts.py
backend/tests/test_handouts_ingest.py
frontend/src/pages/Handouts.tsx
docs/ARCHITECTURE.md
NEXT-STEPS.md

## Out of scope (BACKLOG)

- Transcript passages feeding ask-mode answers (needs prompt work + eval protection).
- Knowledge-map extraction over transcripts (Qwen hours; decide later).
- Deduplicating the triplicate MacWhisper copies inside search results.
