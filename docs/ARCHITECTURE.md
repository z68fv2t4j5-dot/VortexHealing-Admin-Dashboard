# Architecture map

last_reviewed: 2026-10-20

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
| `backend/handouts_service.py` | Handouts text extraction, chunking, embeddings and search | this map, Handouts flow |
| `backend/seed_*.py` | Imports students and classes from files outside the repository | AGENTS.md Part B (data) |
| `backend/tests/` | pytest suite; email campaign API so far | AGENTS.md Part B (test) |
| `docs/CLASS_RULES.md` | Class prerequisites and reminder timing (draft) | itself |

<!-- verify: exists backend/app/api/email_campaigns.py -->
<!-- verify: exists backend/handouts_service.py -->
<!-- verify: exists frontend/src/pages/Email.tsx -->
<!-- verify: exists docs/CLASS_RULES.md -->

## Flows

1. Student import: `All Contacts/*.csv` (outside repo) -> `backend/seed_students.py` -> `students` table -> `/api/students` -> Students page. Files: `backend/seed_students.py`, `backend/app/api/students.py`.
2. Email campaign: Email page composer -> `POST /api/email/preview` (live recipient count from tags/lists) -> `POST /api/email/campaigns` (draft) -> `POST /api/email/send?campaign_id=` -> status `sent` and one `email_recipients` row per student. Files: `frontend/src/pages/Email.tsx`, `backend/app/api/email_campaigns.py`.
3. Handouts: 100 PDF/DOC handouts -> text -> ~500-char chunks -> `all-MiniLM-L6-v2` embeddings -> `backend/handouts_index.json` (154 MB, gitignored) -> `GET /api/handouts/search` (cosine score 0-100, +20 filename match, +10 text match) and `POST /api/handouts/ask` (top chunks to Qwen). The index loads at startup; `/api/handouts/reload` rebuilds it.
4. AI features: Chat, Tasks and Handouts call LM Studio at `localhost:1234/v1`; pages must handle it being down.

## Boundaries and invariants

- **Student data stays on this machine.** No `.db`, `.csv`, `.xlsx` or `.numbers` file is committed; the repository is public. Bought by: ADR-0002.
  <!-- verify: present '^\*\.db$' in .gitignore -->
- **Email send records, it does not deliver.** `/api/email/send` marks the campaign `sent` and writes `email_recipients` rows with status `pending`; no mail transport is wired up yet. Bought by: Phase 1 scope in `docs/EMAIL_CAMPAIGN_PLAN.md`.
  <!-- verify: absent 'smtplib|sendgrid|nodemailer' in backend/app -->
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
- Reminder scheduler and "reminders due" panel: add when `docs/CLASS_RULES.md` is verified and a class-completion source is chosen.
- Frontend tests: add when a page grows logic beyond calling the API.
