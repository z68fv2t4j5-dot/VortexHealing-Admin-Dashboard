# ADR-0002: SQLite and local-only student data

**Status:** Accepted. **Date:** 2026-10-05. **Trigger:** choosing a database for a one-person admin tool that holds student contact details.

## Context

The dashboard holds names, emails and class history for about 1,800 students. It runs on one Mac. A database server (Postgres in Docker) adds setup and a service to keep running, and the data has no reason to leave the machine.

## Decision

Use SQLite in `backend/vortexhealing.db`. Import student and class data from files outside the repository. Never commit the database or the source spreadsheets.

## Consequences

- No concurrent multi-user access; fine for one admin.
- `create_all` does not migrate: a changed model needs its table rebuilt by hand, after a backup.
- Because the repository is public, `.gitignore` must keep every data file type out.

## Alternatives rejected

- Postgres in Docker: server to run for no gain at this size.
- A hosted database: student data would leave the machine.
