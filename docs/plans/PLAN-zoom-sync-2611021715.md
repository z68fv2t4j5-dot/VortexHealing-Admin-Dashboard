# Plan (feature): zoom-sync
Status: done 2026-11-02 (approved by Daniel with the three recommended answers: pull from time to time, unfamiliar topics to `_inbox/`, run by hand)

Departures: routing ignores every underscore folder, not only `_inbox/` (the review found that a set-aside folder of duplicates would make each topic look ambiguous); a transcript with no captions is kept as `.vtt` and recorded in the manifest, with no Markdown; the map gained two invariants (UUID identity; the app never imports the import code) and memory a pointer page.

## Why

Daniel's Zoom classes and healing sessions keep producing transcripts. The first import (2026-10-27 to 11-02) ran from loose scripts in the transcripts folder, outside any repository: six Python scripts and one AppleScript, four downloader variants written while finding a path that worked, a hard-coded personal folder and account address, no tests. The next import would start by re-deriving which script to run. Daniel chose on 2026-11-02 to keep the transcription pipeline in this repository rather than in a separate one.

## Observed

- The path that works for recent meetings: the report API lists meeting instances (six months back at most) -> `GET /meetings/{uuid}/transcript` -> `.vtt` -> Markdown with consecutive captions from one speaker merged into paragraphs.
- Older history needed the Zoom portal's own list, harvested in Safari through AppleScript. One-off, done.
- 68 duplicates came from two file-name stamp formats (`HHMM` and a five-digit variant). 19 kept files still carry the five-digit stamp, so a file-name check would download them again. The download manifest records each meeting UUID.
- Measured while planning: the manifest's 436 rows hold 279 distinct UUIDs, and every set of rows sharing a UUID points at byte-identical files. The portal lists some meetings twice, but the API returns one transcript per UUID, so the first import saved one transcript under two or three names (the portal-list run stamped the meeting start, the UUID-file run the transcript's creation time). The Zoom teacher folder holds 368 files and 279 distinct bodies: 89 extra copies, each in the same subfolder as its twin. One UUID, one transcript: the UUID is the only safe key.
- File-name stamps from the portal-list run equal the report API's UTC start time, so `HHMM` is UTC.
- The import folder holds the staging `.vtt` files and manifest; the indexer already skips it (`zoom-import`).
- The sort into class, healing-event and other folders was done by hand with an agent; no script survived.

## Assumed

- The existing Server-to-Server app and its scopes keep working; the report API needs the account's user ID, which comes from a setting.
- Daniel wants to pull new transcripts from time to time (open question 1).

## Acceptance criteria

1. `cd backend && python -m transcript_import zoom` lists the last six months of meeting instances, downloads only transcripts whose meeting UUID is not in the manifest, converts each to Markdown in the existing format, and prints counts: instances listed, downloaded, already had, unavailable.
2. A new transcript whose topic matches existing transcripts in exactly one subfolder of the Zoom destination goes into that subfolder; any other goes into `_inbox/` there, which the indexer skips until Daniel sorts it.
3. Running it twice in a row downloads nothing the second time; the 19 five-digit files are not downloaded again.
4. `--dry-run` prints what would be downloaded and where it would go, and writes nothing.
5. The credentials file path, the account user ID and the destination folder come from settings; no folder, address, topic or transcript text appears in code, tests or docs.
6. The backend starts unchanged when the new settings are absent; the command exits non-zero with a message naming the missing setting.

## Surface

- `backend/app/core/config.py` (optional `ZOOM_CREDENTIALS`, `ZOOM_USER_ID`, `ZOOM_FOLDER`)
- `backend/.env.example`
- `backend/transcript_import/__init__.py`
- `backend/transcript_import/__main__.py`
- `backend/transcript_import/zoom.py`
- `backend/tests/test_transcript_import_zoom.py`
- `docs/adr/0009-transcript-import-in-this-repository.md`, `docs/adr/README.md`
- `docs/ARCHITECTURE.md` (layout row, flow)
- `NEXT-STEPS.md` (also records that PR #13 merged)
- this plan; the session log

## Design

- One module, `zoom.py`, about 150 lines, standard library only (`urllib`, as today): the existing `ZoomClient` (token refresh, 429/401 back-off, download) carried over; `instances()` from the report API; `fetch(uuid)`; `to_markdown()` carried over with its output format unchanged; `destination(topic)` for the folder; `sync(dry_run)` tying them together.
- Dedupe by meeting UUID from the existing manifest, not by file name; new file names use the `YYYY-MM-DD HHMM — <topic>` stamp the kept files mostly use, `HHMM` being the UTC start. An existing file is never overwritten: a clashing name gets ` (2)`.
- Staging `.vtt` files and the manifest stay in `TRANSCRIPTS_DIR/zoom-import/`; Markdown goes to the teacher folder under `TRANSCRIPTS_DIR` named by `ZOOM_FOLDER` (a person's folder, so a setting, not a constant).
- A package of its own, not inside `handouts/`: it writes into `TRANSCRIPTS_DIR` from an outside API, while `handouts` only reads it; the MacWhisper export (next work item) joins it as `macwhisper.py`.
- Not carried over: the cloud-recordings walker, the meeting-instance walker, the UUID-file and portal-list downloaders and the AppleScript. They served the one-off history import and stay in the local import folder.
- The next Handouts scan (at backend start or Rescan) indexes the new files; the indexer does not change.

## Test plan

- Unit, with a fake client (no network) and invented text: a new UUID is downloaded and converted; a UUID already in the manifest is skipped even when its file name stamp differs; a 404 or a missing download URL counts as unavailable without stopping the run; `--dry-run` writes nothing; topic routing (one matching folder -> that folder, none or several -> `_inbox/`); caption merging by speaker; the stamp format; missing settings -> exit non-zero naming the setting.
- e2e: one real run on Daniel's Mac, `--dry-run` first, then for real; counts only in the session log.
- Coverage: CI measures `--cov=app`, so the new package is outside the diff-coverage count until the tooling PR in NEXT-STEPS adds it; its tests run in CI either way.

## Records

Architecture map delta: yes (layout row; a transcript-import flow). ADR: yes, 0009, because where the import code lives constrains the MacWhisper work that follows.

Cross-repo impact: none.

## Open questions

1. Does Daniel want to pull new Zoom transcripts from time to time? Recommended: yes; it is the only reason to bring the code in. If no, carry nothing over and deactivate the Zoom app.
2. Where do transcripts with an unfamiliar topic go? Recommended: `_inbox/`, out of search until sorted, because healing-event transcripts are confidential and sorting them matters; familiar topics are routed automatically.
3. Run by hand or on a schedule? Recommended: by hand for now; a login item can follow once the command has run cleanly a few times.

## BACKLOG

- 89 duplicate Zoom transcripts in the teacher folder (the 19 five-digit files among them) double the hits in transcript search. Moving the extra copies to an underscore folder, keeping in each set the copy stamped with the meeting start, is a data change outside the repository, Daniel's call.
