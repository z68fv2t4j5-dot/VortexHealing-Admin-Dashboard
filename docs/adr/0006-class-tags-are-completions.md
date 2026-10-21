# ADR-0006: Full-word class tags are the record of completed classes

**Status:** Accepted. **Date:** 2026-10-21. **Trigger:** class eligibility and reminders need to know which classes each student has completed, and the database has no completions table.

## Context

Student tags come from the contacts export. They mix full class names (Foundational, Magical Structures, Sensing I, Omega, Jewel) with abbreviations and dated event codes (SRA, CV+, MS-Cert, 26-01-DM, 23-12-CKC). Daniel scoped email work to the full-word class tags. Read as completions, and with a completed class implying the chart class it hangs off, those tags reproduce the existing "Next Eligible Class" spreadsheet for 120 of 128 APAC Wizards students.

## Decision

Treat a student's full-word class tags, mapped through `backend/app/class_rules.py`, as their completed classes. Ignore abbreviated and dated tags until their meanings are confirmed.

## Consequences

- No new table or import; completions update whenever the contacts CSV is re-seeded.
- Completions recorded only in abbreviated tags are missed (3 of 128 in the check), so a few students will be offered a class they have already done until their tags are fixed or the abbreviations are mapped.
- Students with no class tags are treated as new and offered Foundational Training, except that everyone on the APAC Wizards list counts as having completed it.

## Alternatives rejected

- Import each class attendee list into a completions table: more accurate, but a new import to maintain; revisit if tag gaps cause wrong reminders.
- Guess the abbreviations: a wrong guess sends reminders to the wrong people.
