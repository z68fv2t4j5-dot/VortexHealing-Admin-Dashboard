# NEXT-STEPS

Rewritten at every `harness-close`. Assume the next session knows nothing that is not written here. Read this after `docs/memory/MEMORY.md` and `docs/ARCHITECTURE.md`. Plans in `docs/plans/` are dated snapshots of intent; this file is the current state. If they disagree, this file is right.

## What is true now (measured 2026-10-23)

- Backend suite: 91 tests (email campaign API, class rules, reminders, handouts), run by `cd backend && python -m pytest`.
- Handouts knowledge base, story 1 of `docs/plans/PLAN-handouts-knowledge-base-2610212112.md` (ADR-0008): `backend/handouts/` keeps one current file per handout (74 indexed, 16 older versions retired, 1 identical duplicate skipped), splits them into 1,691 sections and 2,358 passages, and searches by keywords plus nomic embeddings. Index, glossary, notes and eval questions live in `HANDOUTS_KB_DIR` (`~/Documents/Handouts-KB`), outside the repository. Daniel's 21 eval questions: 21/21 find an expected handout in the top 5.
- Handouts page: one box with Auto / Search / Ask; Ask answers through Qwen with `[n]` citations; Rescan picks up new or revised handouts. A full index build takes about 30 seconds; the startup scan skips unchanged files.
- Class prerequisites come from the flowchart in `backend/app/class_rules.py`; completed classes come from full-word class tags (ADR-0006). APAC Wizards count as having done Foundational.
- Email page: APAC Wizards list and full-word class tags only; a "Reminders due" panel (ADR-0007). `/api/email/send` records a send; it does not deliver mail.
- Raw agent transcripts stay on this machine (ADR-0005); session logs carry no student names, emails or handout text.

## Step 0: re-verify before acting on anything above

1. `python scripts/harness_lint.py`
2. `git status --short && git log --oneline -3`
3. `cd backend && python -m pytest -q`
4. `cd backend && python -m handouts status` shows the counts above; `python -m handouts eval` prints the hit total.
5. `curl -s localhost:8000/api/handouts/status` (backend running) returns `"configured": true`.

## Open threads

- Handouts story 2 (answers): sub-query planning, follow-up rewriting, stricter citation checks; then story 3 (knowledge map, overnight extraction with Qwen) and story 4 (teacher notes). Prompts for the local agent live in `~/Documents/Handouts-KB/QWEN-PROMPTS.md`; in story 1 Qwen could not finish its steps, so plan on Claude building or closely supervising.
- Known answer weakness: "what class do you get LifeEssences?" returns a hedged answer although the MF review's overview says "in this class"; stories 2-3 address it.
- Classes page shows wrong prerequisites: `backend/seed_classes.py` predates the flowchart; regenerate its `prerequisites` from `class_rules.py` (back up the database before reseeding).
- Email delivery: approving a reminder or campaign only records it. Decide the sending account; the approval step stays.
- Tooling fixes in their own PRs: `tsc` fails on `tsconfig.json` (TS5070), ESLint 9 cannot read the legacy config, CI should add `--cov=handouts`.
- Parked retrospective: BMAD's `bmad-retrospective` skill fails to install (bmad-code-org/BMAD-METHOD#3130). When fixed: `npx skills add bmad-code-org/BMAD-METHOD -a codex -s bmad-retrospective -y`, rename `_bmad/custom/bmad-retrospective.toml.parked` back to `.toml`, restore the enforcement on "Prune on schedule" in AGENTS.md Part A (bump the version).
- Old `/api/emails` router (`backend/app/api/emails.py`) uses fields the `EmailCampaign` model no longer has; nothing calls it. Remove or fix.
- `backend/handouts_index.json` (154 MB, gitignored) is v1's index and is no longer read; Daniel may delete it.

## Traps, in the order they will bite

1. `python3` must be 3.11+; on this Mac that relies on `~/.local/bin` being first on PATH (set in `~/.zshrc`).
2. Every new key in `backend/.env` needs a field on `Settings` in `backend/app/core/config.py` first; that class forbids unknown keys and the whole backend fails to start.
3. Port 8000 may be held by a static file server started in `~/Documents/Finance`; the dashboard frontend proxies `/api` to 8000, so stop it before running the backend.
4. LM Studio: load `qwen/qwen3.8-27b` at 49152 context and `text-embedding-nomic-embed-text-v1.5`; without the embedder, search falls back to keywords. In Continue, Qwen needs `maxTokens: 12000` and `reasoning_effort: low` or it spends its whole reply thinking.
5. Never commit a check that reads real student data or handout text; run it outside the repository and record only counts.
6. Changing a model does not change its existing table; back up `backend/vortexhealing.db` and rebuild the table.

## Kickoff text (paste into the next session)

> Read NEXT-STEPS.md in full, then AGENTS.md, then docs/memory/MEMORY.md, then docs/ARCHITECTURE.md. Run harness-open. Then: ask Daniel whether to continue with handouts story 2 (answers) or plan real email delivery.
