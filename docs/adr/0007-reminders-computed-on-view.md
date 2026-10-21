# ADR-0007: Class reminders are worked out on view and approved by a person

**Status:** Accepted. **Date:** 2026-10-21. **Trigger:** class reminders at 2 months, 1 month and 2 weeks before each class needed automating without risking an unattended email to students.

## Context

Reminders were tracked as calendar alerts; each one meant working out by hand who was eligible. The dashboard can now work out eligibility (`class_rules.py`). It runs on one Mac that is not always on, and real mail delivery is not wired up yet.

## Decision

Do not run a background scheduler. Whenever the Email page is opened, `GET /api/reminders/due` works out which reminders have arrived and who is eligible. A reminder is offered from its date for 7 days, then dropped, never sent late. Daniel reviews each one and edits the text; "Approve & send" records it as one sent campaign with a recipient row per student, plus a `class_reminders` row (unique per class and stage) so it cannot be approved twice.

## Consequences

- Nothing reaches students without a click, even once mail delivery exists.
- A reminder is only seen when the Email page is opened; if the app is not opened for over a week, that reminder is missed. The 7-day window is the cost of never sending late.
- Recipients are worked out again at approval time, so the list reflects the tags at that moment, not when the reminder first appeared.

## Alternatives rejected

- A cron job or background task that sends on the date: sends unattended, and needs a process kept running on a laptop.
- Pre-creating draft campaigns for every reminder date: drafts would hold stale recipient lists and clutter the history.
