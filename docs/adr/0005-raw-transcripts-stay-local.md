# ADR-0005: Raw agent transcripts stay local

**Status:** Accepted. **Date:** 2026-10-21. **Trigger:** the harness copies raw agent transcripts into the repository, and agents in this project read the student database and contact spreadsheets.

## Context

The harness keeps the conversation record in the repository: a written session log plus the raw transcript copied by `scripts/save_transcript.py`. A raw transcript holds everything the agent saw, including student names and email addresses from queries and spreadsheets, and sometimes keys from config files it read. This repository is on GitHub, and ADR-0002 keeps student data on this machine. A private repository would still put the data on GitHub.

## Decision

Gitignore `docs/sessions/raw/`. `save_transcript.py` still copies transcripts there, so they exist on this machine next to the code. The committed record is the session log, which is written deliberately and carries no student contact details.

## Consequences

- Anyone cloning the repository gets session logs but not raw transcripts; the full conversation exists only on this Mac and is lost with it unless backed up.
- Session logs must be written with care: counts and anonymised examples, never names or emails.
- Part A section 8 of AGENTS.md now differs from the kit; a kit upgrade must keep this change.

## Alternatives rejected

- Commit transcripts to a private repository: student data would still leave the machine.
- Scrub transcripts before committing: personal data in free text cannot be removed reliably.
- Stop copying transcripts at all: loses the local record the harness relies on for review.
