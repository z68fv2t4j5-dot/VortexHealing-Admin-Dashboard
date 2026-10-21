# Plan (feature): reminders due, approved by a person
Status: done 2026-10-21. Departures: none. Daniel's answers: 7-day window, panel on the Email page, approval records the send immediately.

## Investigation

Observed:
- 25 classes in the `classes` table start on or after today; their names map to flowchart classes through `class_rules.class_for`.
- Reminder timing (`docs/CLASS_RULES.md` section 3, from the APAC reminder calendar): 2 months, 1 month and 2 weeks before a class starts, at 09:05 Australia/Sydney.
- `class_rules.completed_from_tags` and `is_eligible` already answer who may take a class. Email scope is the APAC Wizards list only.
- `/api/email/send` works out recipients from a campaign's tags and lists. A reminder's recipients ("APAC Wizards eligible for class X and not yet done it") cannot be expressed that way.
- Sending only records; no mail is delivered (architecture map, invariants).
- Example as of today: Clearing the Kundalini Channel's 2-week reminder fell on 17 October and was never sent; the next ones fall on 27, 28 and 29 October.

Assumed:
- Each stage (2 months, 1 month, 2 weeks) goes to everyone eligible at that moment, even if they got the earlier stage.
- No enrolment data exists, so "already enrolled" cannot be excluded yet; only "already completed" can.

## Acceptance criteria

1. The Email page shows a "Reminders due" panel listing every class whose reminder date has arrived and whose reminder has not been approved, with the stage, the class date, how many APAC Wizards are eligible, and a few sample names.
2. Opening a reminder shows a pre-filled subject and body (class name, dates, stage) that can be edited, and the full recipient count.
3. "Approve & send" records the reminder as sent to exactly those students (one campaign in the history, one recipient row each). It then disappears from the panel. Nothing is ever recorded without that click.
4. A reminder is offered from its date until 7 days after it; after that it is dropped, not sent late.
5. A reminder cannot be approved twice (same class and stage).

Surface: backend/app/reminders.py (new), backend/app/api/reminders.py (new), backend/app/models.py (new ClassReminder table), backend/main.py (mount router), backend/tests/test_reminders.py (new), frontend/src/components/RemindersDue.tsx (new), frontend/src/pages/Email.tsx (render the panel), docs/CLASS_RULES.md, docs/ARCHITECTURE.md, docs/adr/0007-reminders-computed-on-view.md (new), docs/adr/README.md, NEXT-STEPS.md, docs/sessions/session_<stamp>.md, this plan.

## Design

- `reminders.py`: one pure function, `due_reminders(classes, students, approved, today)` -> list of (class, stage, reminder date, eligible students). Pure so it is tested without a database or a clock.
- No background scheduler. The panel works out what is due whenever it is opened. Nothing can send unattended, and there is no process to keep running (ADR-0007).
- New table `class_reminders` (class_id, stage, campaign_id, approved_at), unique on (class_id, stage). It is a new table, so `create_all` makes it with no rebuild. It is what stops a second approval and what drops a reminder from the panel.
- `GET /api/reminders/due` returns the panel's list. `POST /api/reminders/approve` {class_id, stage, subject, body} works out the recipients again on the server, creates the campaign with status `sent`, its recipient rows and the `class_reminders` row, in one transaction. The existing `/api/email/send` is untouched.
- "Today" is the date in Australia/Sydney (`zoneinfo`, standard library).
- `RemindersDue.tsx`: a list plus one modal in the Tasks.tsx pattern; it lives in `components/` because Email.tsx is already long.

## Test plan

Unit (`due_reminders`, synthetic data): all three stage dates; offered from the date through day 7, not before and not after; approved reminders excluded; only eligible APAC Wizards who have not completed the class; a class not on the flowchart is skipped; a past class is ignored.
API: approve creates one campaign with status `sent`, N recipient rows and a `class_reminders` row; a second approve of the same class and stage is refused (409); the due list no longer shows it.
E2E: n/a, the frontend has no test runner; manual check in the browser.

Architecture map delta: yes (new flow, new table). ADR: yes, 0007 (no background scheduler; a person approves each reminder).
Cross-repo impact: none.

## Open questions

1. Grace window: offer a reminder for 7 days after its date, then drop it? [Recommended: yes. Today that would still offer Clearing the Kundalini's 2-week reminder, 4 days late.]
2. Where should the panel live? [Recommended: at the top of the Email page. Dashboard could show a count later.]
3. Should approval record the reminder as sent straight away, or create a draft to send from the history? [Recommended: straight away, after the confirm step. It is one reminder, and the confirm screen already shows the count.]

## BACKLOG

- Real mail delivery: still none; approving records only.
- Enrolment data, to exclude students already booked into a class.
- `backend/seed_classes.py` prerequisites column still predates the flowchart.
