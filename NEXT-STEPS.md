# NEXT-STEPS

Rewritten at every `harness-close`. Assume the next session knows nothing that is not written here. Read this after `docs/memory/MEMORY.md` and `docs/ARCHITECTURE.md`. Plans in `docs/plans/` are dated snapshots of intent; this file is the current state. If they disagree, this file is right.

## What is true now (measured 2026-10-23)

- Backend suite: 136 tests (email campaign API, class rules, reminders, handouts), run by `cd backend && python -m pytest`.
- Handouts knowledge base, story 1 of `docs/plans/PLAN-handouts-knowledge-base-2610212112.md` (ADR-0008): `backend/handouts/` keeps one current file per handout (74 indexed, 16 older versions retired, 1 identical duplicate skipped), splits them into 1,691 sections and 2,358 passages, and searches by keywords plus nomic embeddings. Index, glossary, notes and eval questions live in `HANDOUTS_KB_DIR` (`~/Documents/Handouts-KB`), outside the repository. Daniel's 21 eval questions: 21/21 find an expected handout in the top 5.
- Handouts page: one box with Auto / Search / Ask; Rescan picks up new or revised handouts. A full index build takes about 30 seconds; the startup scan skips unchanged files.
- Handouts story 2 (answers): follow-ups are rewritten and multi-part questions split (Qwen, thinking off), Qwen answers with low thinking and `[n]` citations, under-cited answers are withheld, and the page streams: passages in about 1 s, a simple answer done in about 15-25 s, a multi-part one in about 45 s. `python -m handouts eval --answers` writes a marking sheet to `HANDOUTS_KB_DIR/eval/`.
- Class prerequisites come from the flowchart in `backend/app/class_rules.py`; completed classes come from full-word class tags (ADR-0006). APAC Wizards count as having done Foundational.
- Email page: APAC Wizards list and full-word class tags only; a "Reminders due" panel (ADR-0007). `/api/email/send` records a send; it does not deliver mail.
- Raw agent transcripts stay on this machine (ADR-0005); session logs carry no student names, emails or handout text.

## Step 0: re-verify before acting on anything above

1. `python scripts/harness_lint.py`
2. `git status --short && git log --oneline -3`
3. `cd backend && python -m pytest -q`
4. `cd backend && python -m handouts status` shows the counts above; `python -m handouts eval` prints the hit total; `curl -s localhost:8001/api/handouts/status` shows the knowledge map's entries and facts.
5. `curl -s localhost:8001/api/handouts/status` (backend running) returns `"configured": true`.

## Open threads

- Handouts story 3 (knowledge map): 6,331 entries and 13,551 facts built by Qwen from 1,370 sections (about 3.5 hours, 4 at a time; cached, so re-indexing does not repeat it). Cards on the page, a Browse tab, and answers that use the map; `python -m handouts extract-knowledge` reads only new or changed sections, `apply-knowledge` rebuilds from the cache.
- Handouts story 4 (teacher notes): notes live as Markdown files in `HANDOUTS_KB_DIR/notes`; the Handouts page has "Add a note" on answers and cards and a Notes tab (edit, delete). Ten notes so far (two from 2026-10-21/24 and eight from Daniel's marking on 2026-10-25); each question they target now answers as Daniel expects. A local marking page (`eval/answers-*-marking.html`, made from a sheet) lets Daniel mark answers with buttons and paste the result. The plan's four stories are done.
- Daniel is checking `~/Documents/Handouts-KB/handout_classes.yaml` (which class each handout belongs to; Sensing Review is set to Sensing I).
- Daniel is marking the answer sheets from `python -m handouts eval --answers` (latest in `~/Documents/Handouts-KB/eval/`); turn his "wrong" marks into fixes: retrieval or prompt where the handouts say it, a teacher note where they do not.
- Ideas Daniel deferred: answer feedback (thumbs) to grow the eval set, audio transcription (the EarthWorks recordings), class-gated access for students. `~/Documents/Handouts-KB/QWEN-PROMPTS.md` is out of date: Qwen could not finish story 1, and stories 1-4 were built by Claude.
- The Tasks page's AI call (`backend/app/api/ai_tasks.py`) names its model `"qwen"`; use `settings.QWEN_MODEL` or LM Studio may load a second copy.
- Classes page shows wrong prerequisites: `backend/seed_classes.py` predates the flowchart; regenerate its `prerequisites` from `class_rules.py` (back up the database before reseeding).
- Email delivery: approving a reminder or campaign only records it. Decide the sending account; the approval step stays.
- Tooling fixes in their own PRs: `tsc` fails on `tsconfig.json` (TS5070), ESLint 9 cannot read the legacy config, CI should add `--cov=handouts`.
- Parked retrospective: BMAD's `bmad-retrospective` skill fails to install (bmad-code-org/BMAD-METHOD#3130). When fixed: `npx skills add bmad-code-org/BMAD-METHOD -a codex -s bmad-retrospective -y`, rename `_bmad/custom/bmad-retrospective.toml.parked` back to `.toml`, restore the enforcement on "Prune on schedule" in AGENTS.md Part A (bump the version).
- Old `/api/emails` router (`backend/app/api/emails.py`) uses fields the `EmailCampaign` model no longer has; nothing calls it. Remove or fix.
- `backend/handouts_index.json` (154 MB, gitignored) is v1's index and is no longer read; Daniel may delete it.

## Traps, in the order they will bite

1. `python3` must be 3.11+; on this Mac that relies on `~/.local/bin` being first on PATH (set in `~/.zshrc`).
2. Every new key in `backend/.env` needs a field on `Settings` in `backend/app/core/config.py` first; that class forbids unknown keys and the whole backend fails to start.
3. The dashboard backend runs on port 8001, because Daniel's finances app uses 8000. Pages must call relative `/api` URLs; a hard-coded `localhost:8000` reaches the wrong app.
4. LM Studio: load `qwen/qwen3.8-27b` at 49152 context and `text-embedding-nomic-embed-text-v1.5`; without the embedder, search falls back to keywords. Call the model by that exact identifier: `qwen3.8-27b` without `qwen/` made LM Studio load a second, slower copy (`lms ps` shows it; `lms unload qwen3.8-27b` removes it). In Continue, Qwen needs `maxTokens: 12000` and `reasoning_effort: low` or it spends its whole reply thinking.
5. Never commit a check that reads real student data or handout text; run it outside the repository and record only counts.
6. Changing a model does not change its existing table; back up `backend/vortexhealing.db` and rebuild the table.

## Kickoff text (paste into the next session)

> Read NEXT-STEPS.md in full, then AGENTS.md, then docs/memory/MEMORY.md, then docs/ARCHITECTURE.md. Run harness-open. Then: ask Daniel for his marks on the latest answer sheet in `~/Documents/Handouts-KB/eval/`, and whether to plan real email delivery next or improve the handouts from his marks.
