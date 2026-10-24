# Architecture map

last_reviewed: 2026-10-23

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
| `backend/seed_*.py` | Imports students and classes from files outside the repository | AGENTS.md Part B (data) |
| `backend/tests/` | pytest suite; email campaign API so far | AGENTS.md Part B (test) |
| `backend/app/class_rules.py` | Flowchart prerequisites as data; completed classes from tags; eligibility; next class | `docs/CLASS_RULES.md`, ADR-0006 |
| `backend/app/reminders.py`, `backend/app/api/reminders.py` | Which reminders are due and to whom; approve records one sent campaign | ADR-0007 |
| `frontend/src/components/HandoutsKnowledge.tsx` | Knowledge-map cards and the Browse tab on the Handouts page | ADR-0008 |
| `frontend/src/components/HandoutsNotes.tsx` | Teacher-note editor and the Notes tab on the Handouts page | ADR-0008 |
| `frontend/src/components/RemindersDue.tsx` | "Reminders due" panel at the top of the Email page | ADR-0007 |
| `docs/CLASS_RULES.md` | How to read the flowchart, decisions on unusual boxes, reminder timing | itself |

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
3. Handouts: `HANDOUTS_DIR` -> `catalog.build_catalog` (one current file per handout; retired, skipped and undecided files listed) -> `extract_text` (`textutil` for .doc/.docx, `pypdf`) -> `sections.split`/`chunk` (heading paths, 250-400 word chunks) -> `kb.sqlite` in `HANDOUTS_KB_DIR` (FTS5 + nomic embeddings from LM Studio) -> `retrieve.search` (glossary expansion, BM25 + vectors fused by RRF, max 3 passages per handout) -> for questions, `answer.ask`: follow-ups rewritten and multi-part questions split by Qwen with thinking off, passages from every search fused (8, or 10 for multi-part), Qwen answers with low thinking from a prompt carrying Daniel's glossary, citations checked (fewer than half the paragraphs cited -> answer withheld) -> `POST /api/handouts/query/stream` (newline-delimited JSON: sources, thinking, text, done) -> Handouts page, which shows passages at once and the answer as it is written. Knowledge map (`knowledge.py`): `python -m handouts extract-knowledge` (or the page's Build button) has Qwen read each section once with thinking off into `extraction_cache` (keyed by section text hash, so re-indexing never repeats the work); `apply` derives `entities`, `entity_definitions` and `facts` (predicates `introduced_in`, `done_in_class`, `releases`, `is_source_of`, `is_part_of`, `requires`, `located_in`, `related_to`; class names resolved against the flowchart and `handout_classes.yaml`). Questions that name an entity get its card, the passages behind its key facts, and a cited "Knowledge map" list in the prompt; the page's Browse tab lists every entry. Teacher notes (`notes.py`): Markdown files with front matter in `HANDOUTS_KB_DIR/notes`, written from the page (`/api/handouts/notes`) or by hand, indexed by every scan as `source_kind = 'note'` (never sent for extraction), boosted by one first-place vote when they match, shown on the cards of the entities they name, always brought into answers about those entities, and cited as "Teacher note"; the prompt makes them override the handouts. Scans are incremental: at backend start (background thread), `POST /api/handouts/rescan`, or `python -m handouts ingest`. Files: `backend/handouts/`, `backend/app/api/handouts.py`, `frontend/src/pages/Handouts.tsx`.
4. Eligibility: student tags -> `class_for` (full-word class tags only) -> `completed_from_tags` (adds the classes each one hangs off) -> `is_eligible` / `next_class` against the `classes` schedule. Files: `backend/app/class_rules.py`. Used by the reminders flow.
5. Reminders: Email page -> `GET /api/reminders/due` (`due_reminders`: each class's 2-month, 1-month and 2-week dates, offered for 7 days, minus approved ones in `class_reminders`; recipients are eligible APAC Wizards who have not done the class) -> person edits and approves -> `POST /api/reminders/approve` -> sent campaign + recipient rows + `class_reminders` row. Files: `backend/app/reminders.py`, `backend/app/api/reminders.py`, `frontend/src/components/RemindersDue.tsx`.
6. AI features: Chat, Tasks and Handouts call LM Studio at `localhost:1234/v1`; pages must handle it being down. Name the model by its LM Studio identifier (`QWEN_MODEL`, default `qwen/qwen3.8-27b`): a bare name makes LM Studio load a second copy at a small context, which tripled answer time.
   <!-- verify: present 'qwen/qwen3.8-27b' in backend/app/core -->

## Boundaries and invariants

- **Student data stays on this machine.** No `.db`, `.csv`, `.xlsx` or `.numbers` file is committed; the repository is public. Bought by: ADR-0002.
  <!-- verify: present '^\*\.db$' in .gitignore -->
- **No handout content inside the repository.** The index, glossary, teacher notes and eval questions live in `HANDOUTS_KB_DIR`; tests use invented text. Bought by: ADR-0008 (the repository is public; handouts are confidential teaching material).
  <!-- verify: absent '/Users/' in backend/handouts -->
- **Email send records, it does not deliver.** `/api/email/send` marks the campaign `sent` and writes `email_recipients` rows with status `pending`; no mail transport is wired up yet. Bought by: Phase 1 scope in `docs/EMAIL_CAMPAIGN_PLAN.md`.
  <!-- verify: absent 'smtplib|sendgrid|nodemailer' in backend/app -->
- **No reminder is recorded without a person's click, and none twice.** There is no background scheduler; `class_reminders` is unique on (class_id, stage). Bought by: ADR-0007.
  <!-- verify: present 'UniqueConstraint\("class_id", "stage"\)' in backend/app -->
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
