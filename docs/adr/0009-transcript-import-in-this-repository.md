# ADR-0009: Transcript import code lives in this repository; the transcripts stay outside it

**Status:** Accepted. **Date:** 2026-11-02. **Trigger:** the first Zoom import ran from loose scripts in the transcripts folder, with no tests and no record of which of four downloaders worked; Daniel wants new Zoom transcripts pulled from time to time, and the 942 unnamed MacWhisper recordings still to be exported. Plan: `docs/plans/PLAN-zoom-sync-2611021715.md`.

## Context

Daniel's class and healing-session transcripts live in `TRANSCRIPTS_DIR`, which this repository already indexes for search (`backend/handouts/transcripts.py`). The code that fills that folder (Zoom downloads, Markdown conversion, sorting) was written ad hoc during earlier sessions, partly outside any repository; the MacWhisper export scripts did not survive at all. The repository is public, the transcripts hold student names and spoken confidences, and the Zoom credentials are secrets. A separate repository with its own harness was offered; Daniel chose this one on 2026-11-02.

## Decision

Import code lives in `backend/transcript_import/` (one module per source: `zoom.py` now, `macwhisper.py` next), run as `python -m transcript_import <source>`. It reads its locations and the credentials file path from settings (`TRANSCRIPTS_DIR`, `ZOOM_CREDENTIALS`, `ZOOM_USER_ID`, `ZOOM_FOLDER`); it writes only under `TRANSCRIPTS_DIR`. Transcripts, staging files, manifests and credentials never enter the repository, and the tests use invented text and a fake Zoom. A downloaded transcript is identified by its Zoom meeting UUID, never by its file name.

## Consequences

- One harness, one CI gate and one set of settings for the whole pipeline; the import code is reviewed and tested like the app.
- Local data tooling (API clients, file shuffling) now sits next to the web app; `transcript_import` must not be imported by `app/`, or the backend would gain network code it does not need.
- CI's coverage measures `app/` only, so the new package's lines are outside the diff-coverage gate until the CI change in NEXT-STEPS lands; its tests run in CI regardless.
- The one-off history-import scripts (portal harvest through Safari, four downloader variants) stay in the local import folder and are not maintained.

## Alternatives rejected

- A separate repository bootstrapped with the harness: a second set of skills, hooks and CI to keep current for a few hundred lines of code.
- Leaving the scripts in the transcripts folder: untested, unversioned, and the next run starts by re-deriving which one works.
- Deduplicating by file name: the first import named the same transcript two or three ways, and 89 copies survived a name-based cleanup.
