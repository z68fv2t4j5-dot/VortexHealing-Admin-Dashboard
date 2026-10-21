# NEXT-STEPS

Rewritten at every `harness-close`. Assume the next session knows nothing that is not written here. Read this after `docs/memory/MEMORY.md` and `docs/ARCHITECTURE.md`. Plans in `docs/plans/` are dated snapshots of intent; this file is the current state. If they disagree, this file is right.

## What is true now (measured 2026-10-21)

- Backend suite: 24 tests (email campaign API and class rules), run by `cd backend && python -m pytest`.
- Class prerequisites are transcribed from the flowchart into `backend/app/class_rules.py`; completed classes come from full-word class tags (ADR-0006). Against the "Next Eligible Class" spreadsheet: 120 of 128 APAC Wizards students match (`docs/CLASS_RULES.md` section 2 explains the 8).
- Email page offers the APAC Wizards list only and full-word class tags only (`GET /api/email/options`). `/api/email/send` records a send; it does not deliver mail.
- Raw agent transcripts stay on this machine (ADR-0005); session logs carry no student names or emails.

## Step 0: re-verify before acting on anything above

1. `python scripts/harness_lint.py`
2. `git status --short && git log --oneline -3`
3. `cd backend && python -m pytest -q`
4. `curl -s localhost:8000/api/email/options` (backend running) lists APAC Wizards and the class tags.

## Open threads

- Reminder scheduler and "reminders due" panel: the next feature. For each scheduled class, at 2 months, 1 month and 2 weeks before, list APAC Wizards students for whom `is_eligible` holds and who have not completed it; a person approves before anything is sent.
- Abbreviated tags: Daniel to confirm meanings (e.g. CKC = Clearing the Kundalini Channel, CV+ = Core Veil, LF, KI, MS, MF, SI, CQ, BT, DM, OG, IP, SOH). Mapping confirmed ones in `ALIASES` would close most of the spreadsheet gap.
- APAC Wizards membership and Foundational: 4 APAC Wizards students have no class tags, and the spreadsheet treats them as having done Foundational. Ask Daniel whether being an APAC Wizard implies Foundational.
- Classes page shows wrong prerequisites: `backend/seed_classes.py` predates the flowchart; regenerate its `prerequisites` from `class_rules.py` (back up the database before reseeding).
- Email delivery: no mail transport; decide the sending account and keep a human approval step before any real send.
- Parked retrospective: BMAD's `bmad-retrospective` skill fails to install (YAML error, reported upstream as bmad-code-org/BMAD-METHOD#3130). When it is fixed: `npx skills add bmad-code-org/BMAD-METHOD -a codex -s bmad-retrospective -y`, rename `_bmad/custom/bmad-retrospective.toml.parked` back to `.toml`, and restore the original enforcement on "Prune on schedule" in AGENTS.md Part A (bump the constitution version).
- Old `/api/emails` router (`backend/app/api/emails.py`) uses fields the `EmailCampaign` model no longer has; nothing calls it. Remove or fix.

## Traps, in the order they will bite

1. `python3` must be 3.11+; on this Mac that relies on `~/.local/bin` being first on PATH (set in `~/.zshrc`).
2. Never commit a check that reads real student data; run it from outside the repository and record only counts in the session log.
3. Changing a model does not change its existing table; back up `backend/vortexhealing.db` and rebuild the table.
4. LM Studio loads models at a small default context; load Qwen with 16384+ or prompts get truncated silently.

## Kickoff text (paste into the next session)

> Read NEXT-STEPS.md in full, then AGENTS.md, then docs/memory/MEMORY.md, then docs/ARCHITECTURE.md. Run harness-open. Then: run harness-plan for the reminder scheduler and "reminders due" panel.
