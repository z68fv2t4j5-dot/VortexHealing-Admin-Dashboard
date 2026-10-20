# NEXT-STEPS

Rewritten at every `harness-close`. Assume the next session knows nothing that is not written here. Read this after `docs/memory/MEMORY.md` and `docs/ARCHITECTURE.md`. Plans in `docs/plans/` are dated snapshots of intent; this file is the current state. If they disagree, this file is right.

## What is true now (measured 2026-10-20)

- Harness adopted at the repository root; `python scripts/harness_lint.py` reports 0 errors.
- Backend suite: 8 tests on the email campaign API, run by `cd backend && python -m pytest`.
- Email page builds campaigns, previews recipients and records sends; `/api/email/send` does not deliver mail yet (see `docs/ARCHITECTURE.md`, invariants).
- Students: 1771 rows, 1769 with a first name (`sqlite3 backend/vortexhealing.db "select count(*), sum(first_name<>'') from students"`).
- `docs/CLASS_RULES.md` is a draft; rows marked ⚠ are unverified.

## Step 0: re-verify before acting on anything above

1. `python scripts/harness_lint.py`
2. `git status --short && git log --oneline -3`
3. `cd backend && python -m pytest -q`

## Open threads

- Class rules: Daniel to correct the ⚠ prerequisite rows and pick the source of class-completion history; the reminder scheduler waits on both.
- Email delivery: no mail transport; decide the sending account and keep a human approval step before any real send.
- Parked retrospective: BMAD's `bmad-retrospective` skill fails to install (YAML error, reported upstream as bmad-code-org/BMAD-METHOD#3130). When it is fixed: `npx skills add bmad-code-org/BMAD-METHOD -a codex -s bmad-retrospective -y`, rename `_bmad/custom/bmad-retrospective.toml.parked` back to `.toml`, and restore the original enforcement on "Prune on schedule" in AGENTS.md Part A (constitution v1.1.2).
- Old `/api/emails` router (`backend/app/api/emails.py`) uses fields the `EmailCampaign` model no longer has; nothing calls it. Remove or fix.

## Traps, in the order they will bite

1. `python3` must be 3.11+; on this Mac that relies on `~/.local/bin` being first on PATH (set in `~/.zshrc`).
2. Changing a model does not change its existing table; back up `backend/vortexhealing.db` and rebuild the table.
3. LM Studio loads models at a small default context; load Qwen with 16384+ or prompts get truncated silently.

## Kickoff text (paste into the next session)

> Read NEXT-STEPS.md in full, then AGENTS.md, then docs/memory/MEMORY.md, then docs/ARCHITECTURE.md. Run harness-open. Then: check whether docs/CLASS_RULES.md has been verified, and if so plan the reminder scheduler.
