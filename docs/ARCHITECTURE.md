# Architecture map

last_reviewed: 2026-11-05

The one living map of this repository: components, flows, boundaries and invariants. Read it before touching unfamiliar code; update it in the same change that moves structure (`harness-close` step 3). It describes this repository only. Each invariant cites the defect or decision that bought it. Factual claims carry a `verify:` line so the lint fails on the commit that makes them false.

## What this repository is

A local admin dashboard for one VortexHealing teacher: student contacts, the class schedule and eligibility, email campaigns, task tracking, and semantic search over class handouts. Everything runs on one Mac; student data never leaves it.

## Layout

| Path | Holds | Owner doc or skill |
|---|---|---|
| `frontend/src/pages/` | One React page per sidebar entry (Students, Classes, Email, Tasks, Handouts, Chat...) | this map |
| `frontend/src/components/Navigation.tsx` | Sidebar | this map |
| `backend/main.py` | FastAPI app; mounts every router under `/api` and creates missing tables at startup | this map |
| `backend/app/models.py` | SQLAlchemy models (students, classes, email campaigns, tasks...) | AGENTS.md Part B (schema) |
| `backend/app/api/` | One router per feature | this map |
| `backend/handouts/` | Handouts knowledge base: catalogue, extraction, sections, SQLite/FTS5 store, embeddings, ingest, hybrid search; CLI `python -m handouts` | ADR-0008, Handouts flow |
| `backend/handouts/transcripts.py` | Class transcripts from `TRANSCRIPTS_DIR` indexed as `source_kind='transcript'`; searched only when asked for, never in answers | `docs/plans/PLAN-transcripts-in-kb-2611021110.md` |
| `backend/transcript_import/` | Fills `TRANSCRIPTS_DIR`: `zoom.py` downloads new Zoom transcripts and files them; CLI `python -m transcript_import zoom [--dry-run]` | ADR-0009, Transcript import flow |
| `backend/seed_*.py` | Imports students and classes from files outside the repository | AGENTS.md Part B (data) |
| `backend/tests/` | pytest suite; email campaign API so far | AGENTS.md Part B (test) |
| `backend/app/class_rules.py` | Flowchart prerequisites as data; completed classes from tags; eligibility; next class | `docs/CLASS_RULES.md`, ADR-0006 |
| `backend/app/reminders.py`, `backend/app/api/reminders.py` | Which reminders are due and to whom; approve records one sent campaign | ADR-0007 |
| `frontend/src/components/HandoutsKnowledge.tsx` | Knowledge-map cards and the Browse tab on the Handouts page | ADR-0008 |
| `frontend/src/components/HandoutsNotes.tsx` | Teacher-note editor and the Notes tab on the Handouts page | ADR-0008 |
| `frontend/src/components/HandoutsImprove.tsx`, `frontend/src/components/AnswerText.tsx` | The Improve tab (test questions, runs, marking, note drafts); answer rendering shared with the page | `docs/plans/PLAN-handouts-improve-2610291801.md` |
| `frontend/src/components/RemindersDue.tsx` | "Reminders due" panel at the top of the Email page | ADR-0007 |
| `backend/app/admin_tasks.py`, `backend/app/api/admin_tasks.py` | Admin tasks worked out from the class schedule and the quarter; Done records a key in `admin_tasks_done` | `docs/CLASS_RULES.md` section 5, ADR-0010 |
| `backend/app/digest.py` | The daily push digest to Daniel's phone through ntfy; CLI `python -m app.digest [--dry-run]`, run hourly by a LaunchAgent outside the repository | ADR-0010, Digest flow |
| `frontend/src/components/AdminTasksDue.tsx` | "From your classes" panel at the top of the Tasks page | ADR-0010 |
| `docs/CLASS_RULES.md` | How to read the flowchart, decisions on unusual boxes, reminder and admin-task timing | itself |

<!-- verify: exists backend/app/api/email_campaigns.py -->
<!-- verify: exists backend/handouts/catalog.py -->
<!-- verify: exists backend/handouts/retrieve.py -->
<!-- verify: absent 'handouts_service' in backend -->
<!-- verify: exists frontend/src/pages/Email.tsx -->
<!-- verify: exists docs/CLASS_RULES.md -->
<!-- verify: exists backend/app/class_rules.py -->

## Flows

1. Student import: `All Contacts/*.csv` (outside repo) -> `backend/seed_students.py` -> `students` table -> `/api/students` -> Students page. Files: `backend/seed_students.py`, `backend/app/api/students.py`.
2. Email campaign: Email page loads `GET /api/email/options` (APAC Wizards list, full-word class tags) -> composer -> `POST /api/email/preview` (live recipient count from tags/lists) -> `POST /api/email/campaigns` (draft) -> `POST /api/email/send?campaign_id=` -> status `sent` and one `email_recipients` row per student. Files: `frontend/src/pages/Email.tsx`, `backend/app/api/email_campaigns.py`.
3. Handouts: `HANDOUTS_DIR` -> `catalog.build_catalog` (one current file per handout; retired, skipped and undecided files listed) -> `extract_text` (`textutil` for .doc/.docx, `pypdf`) -> `sections.split`/`chunk` (heading paths, 250-400 word chunks) -> `kb.sqlite` in `HANDOUTS_KB_DIR` (FTS5 + nomic embeddings from LM Studio) -> `retrieve.search` (glossary expansion, BM25 + vectors fused by RRF, max 3 passages per handout) -> for questions, `answer.ask`: follow-ups rewritten and multi-part questions split by Qwen with thinking off, passages from every search fused (8, or 10 for multi-part), Qwen answers with low thinking from a prompt carrying Daniel's glossary, citations checked (fewer than half the paragraphs cited -> answer withheld) -> `POST /api/handouts/query/stream` (newline-delimited JSON: sources, thinking, text, done) -> Handouts page, which shows passages at once and the answer as it is written. Knowledge map (`knowledge.py`): `python -m handouts extract-knowledge` (or the page's Build button) has Qwen read each section once with thinking off into `extraction_cache` (keyed by section text hash, so re-indexing never repeats the work); `apply` derives `entities`, `entity_definitions` and `facts` (predicates `introduced_in`, `done_in_class`, `releases`, `is_source_of`, `is_part_of`, `requires`, `located_in`, `related_to`; class names resolved against the flowchart and `handout_classes.yaml`). Questions that name an entity get its card, the passages behind its key facts, and a cited "Knowledge map" list in the prompt; the page's Browse tab lists every entry. Teacher notes (`notes.py`): Markdown files with front matter in `HANDOUTS_KB_DIR/notes`, written from the page (`/api/handouts/notes`) or by hand, indexed by every scan as `source_kind = 'note'` (never sent for extraction), boosted by one first-place vote when they match, shown on the cards of the entities they name, always brought into answers about those entities, and cited as "Teacher note"; the prompt makes them override the handouts. Improvement loop (`improve.py`, the Improve tab): test questions in `HANDOUTS_KB_DIR/eval/questions.yaml`; a run asks them all in a background thread and writes `eval/runs/<id>.json` after every answer; Daniel marks each answer; for a correction Qwen (thinking off) drafts a self-contained note in his words, linked to the entries the question names, which he saves in the note editor; a search check counts expected handouts without Qwen. Readiness (`model.py`): the page reads LM Studio's model list and can load the MLX Qwen and the embedder through `lms`; a login item on Daniel's Mac does the same at login (outside the repository). Quick answers (`ask(..., quick=True)`): no split, 6 passages, thinking off, about 120 words. Scans are incremental: at backend start (background thread), `POST /api/handouts/rescan`, or `python -m handouts ingest`. Class transcripts (`transcripts.py`): Markdown files under `TRANSCRIPTS_DIR` (optional; folders starting with `_` and `zoom-import` skipped) indexed by every scan as `source_kind = 'transcript'`, one section per file, family = top folder, date from the file name; searched only when the page's source selector asks for them (`retrieve.search(kinds=...)`, default handouts + notes so the tuned answers never change), served by the file endpoint, never sent for extraction and never cited in answers. Files: `backend/handouts/`, `backend/app/api/handouts.py`, `frontend/src/pages/Handouts.tsx`.
4. Eligibility: student tags -> `class_for` (full-word class tags only) -> `completed_from_tags` (adds the classes each one hangs off) -> `is_eligible` / `next_class` against the `classes` schedule. Files: `backend/app/class_rules.py`. Used by the reminders flow.
5. Reminders: Email page -> `GET /api/reminders/due` (`due_reminders`: each class's 2-month, 1-month and 2-week dates, offered for 7 days, minus approved ones in `class_reminders`; recipients are eligible APAC Wizards who have not done the class) -> person edits and approves -> `POST /api/reminders/approve` -> sent campaign + recipient rows + `class_reminders` row. Files: `backend/app/reminders.py`, `backend/app/api/reminders.py`, `frontend/src/components/RemindersDue.tsx`.
6. AI features: Chat, Tasks and Handouts call LM Studio at `localhost:1234/v1`; pages must handle it being down. Name the model by its LM Studio identifier (`QWEN_MODEL`, default `qwen/qwen3.8-27b`): a bare name makes LM Studio load a second copy at a small context, which tripled answer time.
   <!-- verify: present 'qwen/qwen3.8-27b' in backend/app/core -->
7. Transcript import (Zoom): `python -m transcript_import zoom` -> report API lists the account's meeting instances for the last six months (`ZOOM_USER_ID`, token from the `ZOOM_CREDENTIALS` file) -> UUIDs already in `TRANSCRIPTS_DIR/zoom-import/transcripts_manifest.csv` skipped -> `/meetings/{uuid}/transcript` (404 or not downloadable = unavailable) -> `.vtt` staged in `zoom-import/vtt/`, Markdown (one paragraph per speaker turn) named `YYYY-MM-DD HHMM — <topic>` with the UTC start, written to the one non-underscore `ZOOM_FOLDER` subfolder whose files share the topic, else `_inbox/` -> manifest row. The next handouts scan indexes it (`_inbox/` and `zoom-import/` excepted). Files: `backend/transcript_import/zoom.py`.
   <!-- verify: exists backend/transcript_import/zoom.py -->
8. Digest: LaunchAgent `com.vortexhealing.digest` (on Daniel's Mac, not in the repository) runs `python -m app.digest` in `backend/` at minute 0 of every hour and at login -> before 09:00 Amsterdam time, or when `digest_log` already has today's Amsterdam date, it exits -> otherwise it reads `due_now` (the Email page's due list, Sydney date), upcoming reminder dates, `admin_tasks` (schedule and quarter minus `admin_tasks_done`, Amsterdam date) and hand-added tasks with a due date -> `build` makes one message (today, overdue, coming up in 7 days; recipient counts, never names), or nothing on a day with nothing due today or overdue -> one JSON POST to `NTFY_SERVER` on topic `NTFY_TOPIC` -> a `digest_log` row. A failed POST logs nothing, so the next hour retries. Tasks page: `GET /api/admin-tasks` and `POST /api/admin-tasks/done`; hand-added tasks are marked done through `PUT /api/tasks/{id}`. Files: `backend/app/digest.py`, `backend/app/admin_tasks.py`, `backend/app/api/admin_tasks.py`, `frontend/src/components/AdminTasksDue.tsx`, `frontend/src/pages/Tasks.tsx`.
   <!-- verify: exists backend/app/digest.py -->

## Boundaries and invariants

- **Student data stays on this machine.** No `.db`, `.csv`, `.xlsx` or `.numbers` file is committed; the repository is public. Bought by: ADR-0002.
  <!-- verify: present '^\*\.db$' in .gitignore -->
- **No handout content inside the repository.** The index, glossary, teacher notes and eval questions live in `HANDOUTS_KB_DIR`; tests use invented text. Bought by: ADR-0008 (the repository is public; handouts are confidential teaching material).
  <!-- verify: absent '/Users/' in backend/handouts -->
- **No transcript content inside the repository.** Class and healing-session transcripts hold student names and spoken confidences; they live in `TRANSCRIPTS_DIR`, outside the repository, and transcript tests use invented text. The import code names no folder, account or address; settings do. Bought by: ADR-0005 (raw transcripts stay local), the ADR-0008 pattern and ADR-0009.
  <!-- verify: absent '/Users/|@gmail|Class-Transcripts' in backend/transcript_import -->
- **A Zoom transcript is identified by its meeting UUID, never its file name.** The first import saved one transcript under two or three names. Bought by: ADR-0009.
  <!-- verify: present 'if uuid in have' in backend/transcript_import -->
- **Nothing listens on the network by default.** The backend binds `127.0.0.1:8001` and Vite `localhost:3000`; no route sits behind a login, so another machine reaches the dashboard only when someone runs Vite with `--host`, and then the proxy exposes every API with it. Bought by: 2026-11-03, the backend found on every interface with the Mac's firewall off (`docs/plans/PLAN-backend-local-only-2611031221.md`).
  <!-- verify: absent 'host="0.0.0.0"' in backend -->
- **The app never imports the import code.** `transcript_import` holds API clients and file moves the web backend does not need. Bought by: ADR-0009.
  <!-- verify: absent 'transcript_import' in backend/app -->
- **Email send records, it does not deliver.** `/api/email/send` marks the campaign `sent` and writes `email_recipients` rows with status `pending`; no mail transport is wired up yet. Bought by: Phase 1 scope in `docs/EMAIL_CAMPAIGN_PLAN.md`.
  <!-- verify: absent 'smtplib|sendgrid|nodemailer' in backend/app -->
- **No reminder is recorded without a person's click, and none twice.** `class_reminders` is unique on (class_id, stage). The only scheduled job, the digest, writes `digest_log` alone and never approves or records a reminder or campaign. Bought by: ADR-0007, narrowed by ADR-0010.
  <!-- verify: present 'UniqueConstraint\("class_id", "stage"\)' in backend/app -->
  <!-- verify: absent 'ClassReminder\(|EmailCampaign\(|EmailRecipient\(' in backend/app/digest.py -->
- **The digest carries no student data.** It reaches ntfy.sh, outside this Mac, so it holds class names, recipient counts and Daniel's own task titles only. It gets the recipients through the Email page's `due_now`, uses only how many there are, and never touches a name or address field. Bought by: ADR-0010 and ADR-0002.
  <!-- verify: absent 'first_name|last_name|\.email\b' in backend/app/digest.py -->
- **Tests never touch the real database.** `backend/tests/conftest.py` sets `DATABASE_URL` to in-memory SQLite before the app imports. Bought by: the suite running beside a live `vortexhealing.db`.
  <!-- verify: present 'DATABASE_URL.. = .sqlite://' in backend/tests -->
  <!-- verify: exists AGENTS.md -->
  <!-- verify: exists docs/adr/README.md -->
  <!-- verify: exists docs/memory/MEMORY.md -->
  <!-- verify: exists docs/sessions/README.md -->
  <!-- verify: exists scripts/harness_lint.py -->
  <!-- verify: exists scripts/save_transcript.py -->
  <!-- verify: exists .githooks/pre-commit -->
  <!-- verify: exists .githooks/pre-push -->
  <!-- verify: exists .github/workflows/harness-gates.yml -->

## Deliberately not built yet

- Real email delivery: add when campaigns are ready to go to students (needs a mail account and an approval step).
- Frontend tests: add when a page grows logic beyond calling the API.
