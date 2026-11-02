---
name: transcript-import
description: Transcripts are pulled into TRANSCRIPTS_DIR by python -m transcript_import; a Zoom transcript is its meeting UUID, never its file name; design in ADR-0009
metadata:
  type: project
---

**Fact:** `backend/transcript_import/zoom.py` (`cd backend && python -m transcript_import zoom [--dry-run]`) downloads the last six months of Zoom transcripts whose meeting UUID is not in `zoom-import/transcripts_manifest.csv`, and files each by topic or into `_inbox/`. The MacWhisper export is to join it as `macwhisper.py`.

**Why:** the first import, run from loose scripts, saved one transcript under two or three names.

**Authority:** ADR-0009
