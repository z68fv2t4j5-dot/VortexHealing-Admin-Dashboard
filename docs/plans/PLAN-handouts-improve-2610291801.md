# Plan (feature): handouts improvement loop and a ready, fast Qwen
Status: done 2026-10-29 (Daniel chose options A and B).

Departures, as built:
- The note-draft prompt gets the answer as context and an example: without them Qwen kept terse corrections terse ("Also say it is a 3-day class."); with them, "The InterDimensional Vortex class is a 3-day class."
- `eval --answers` now writes a run for the Improve tab instead of a Markdown sheet; the HTML marking page is no longer needed.
- The readiness line offers "Load models" for whichever of Qwen and the embedder is missing.
- Measured: a quick answer finished in 8 s (first words at 4.7 s) where the full answer took 15 s for the same question.

## Why

The handouts knowledge base answers entirely on local Qwen, but improving it has needed Claude: marking pages, reading marks, drafting notes from corrections, re-running the test questions. Daniel wants to keep training it himself on the local model. Qwen has also felt laggy: it was found unloaded (LM Studio then loads it on demand with default settings), and full answers take about 30 s.

## Observed (2026-10-29)

- Answers, search, the knowledge map and notes already run locally (Qwen 3.8 27B MLX and nomic in LM Studio).
- Qwen was not loaded until Daniel loaded it by hand (MLX 4-bit, context 33,247, no idle unload). An unloaded model is loaded just in time with default settings and an idle time-out.
- The improvement loop so far: `python -m handouts eval --answers` writes a Markdown sheet; Claude turned it into an HTML marking page; Daniel pasted marks; Claude drafted notes and Daniel approved them. Latest sheet: 21/21 right.
- `eval/questions.yaml` carries comments; a YAML round trip drops them.

## Acceptance criteria

1. An **Improve** tab on the Handouts page lists the test questions (add, edit, delete), runs them all in the background with progress, and shows each answer with Right / Partly right / Wrong buttons and a note box; marks are saved as given.
2. For a Partly or Wrong answer, **Draft a note** has Qwen turn Daniel's correction into a self-contained note in his words, linked to the entries the question names; Daniel edits and saves it in the existing note editor.
3. A history of runs shows date, right / partly / wrong / unmarked and average answer time; a **Search check** shows how many questions find an expected handout (no Qwen needed).
4. Any answer on the page can be added to the test questions with one click.
5. The page shows whether Qwen and the embedder are loaded and offers **Load Qwen**, which loads the MLX model at the configured context with no idle unload.
6. A **Quick answer** mode answers with thinking off, fewer passages and a short reply, in about 5-10 s.
7. On Daniel's Mac, a login item loads both models at the right settings (installed outside the repository, removable).

## Design

- `backend/handouts/improve.py`: test questions (YAML in `HANDOUTS_KB_DIR/eval`, comments moved into a `note` field once), runs as JSON files in `eval/runs/` written after every answer (so progress survives a restart), marks, note drafts (Qwen, thinking off, JSON reply; entries from `knowledge.find_entities`, not from Qwen). The CLI's `eval --answers` uses the same run code.
- `backend/handouts/model.py`: model status from LM Studio's `/api/v0/models`; loading through the `lms` CLI in the background. New settings `LMS_PATH`, `QWEN_LOAD_KEY` (`qwen/qwen3.8-27b@4bit`, the MLX file) and `QWEN_CONTEXT` (32768).
- `answer.ask(..., quick=True)`: no split, 6 passages, thinking off, about 120 words.
- API: `/handouts/eval/questions` (GET, POST, PUT/DELETE by index), `/handouts/eval/runs` (GET, POST to start), `/handouts/eval/runs/{id}` (GET), `/handouts/eval/runs/{id}/items/{n}` (PUT mark), `/handouts/eval/runs/{id}/items/{n}/draft-note` (POST), `/handouts/eval/search-check` (GET), `/handouts/model` (GET), `/handouts/model/load` (POST); query mode `quick`.
- Page: `HandoutsImprove.tsx` (Improve tab), `AnswerText.tsx` (answer rendering shared by the page and the tab), a readiness line with Load Qwen, a Quick answer mode, "Add to test questions" on answers.
- Login item: a script and a LaunchAgent in Daniel's Library folder that start LM Studio's server and load both models; documented in NEXT-STEPS, not in the repository.

No new dependencies. A run uses Qwen for about 10-15 minutes; one run at a time.

Surface: backend/handouts/improve.py, backend/handouts/model.py, backend/handouts/answer.py, backend/handouts/__main__.py, backend/app/api/handouts.py, backend/app/core/config.py, backend/.env.example, backend/tests/test_handouts_improve.py, backend/tests/test_handouts_model.py, backend/tests/test_handouts_answer.py, frontend/src/components/HandoutsImprove.tsx, frontend/src/components/AnswerText.tsx, frontend/src/pages/Handouts.tsx, docs/ARCHITECTURE.md, docs/memory/handouts-knowledge-base.md, NEXT-STEPS.md, docs/plans/PLAN-handouts-improve-2610291801.md, docs/sessions/

Test plan: unit — question CRUD keeps entries and notes; a run records every item, survives a failing answer, refuses a second run; marks validate; the draft uses Daniel's words and the question's entries (Qwen faked); model status reads LM Studio's list and reports down; load builds the right `lms` command; quick mode skips the split and uses thinking off. Mutation per rule. e2e: page driven headless (Improve tab, a run on 2 questions, marking, a draft). Architecture map delta: yes (flow 3). ADR: no (no decision that constrains later work beyond the plan).

BACKLOG: none yet.
