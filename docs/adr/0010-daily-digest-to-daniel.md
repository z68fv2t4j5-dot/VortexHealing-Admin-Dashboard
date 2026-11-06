# ADR-0010: A daily push digest tells Daniel what is due; still nothing reaches students without his click

**Status:** Accepted. **Date:** 2026-11-04. **Trigger:** on 2026-11-04 the Magical Structures 2-week reminder reached the last day of its window without being seen and closed unapproved, the cost ADR-0007 names; Daniel also wanted notice of admin tasks, which had no timing recorded anywhere.

## Context

ADR-0007 works reminders out only when the Email page is opened, and rejects a background scheduler because it would send to students unattended. Daniel lives in Amsterdam; the students and the reminder dates are in Sydney. The dashboard runs on one Mac that is not always awake, and the backend listens on that Mac only, so a phone cannot reach it. Daniel chose, in an interview on 2026-11-04: the ntfy phone app, one digest a day at 09:00 Amsterdam time, a "coming up" section, reminder nudges on days 0, 3 and 7, overdue admin tasks repeated daily until ticked, and admin-task timing per class and per quarter (`docs/CLASS_RULES.md` section 5).

## Decision

Run `python -m app.digest` every hour from a LaunchAgent on Daniel's Mac. Once per Amsterdam day, from 09:00, it reads the reminders due (the Email page's own list), the admin tasks worked out from the schedule, and the hand-added tasks, and publishes one message to a private ntfy.sh topic. The message carries class names, counts and Daniel's own task titles, never a student's name, email address or eligibility list. The job writes only `digest_log`; it never approves, records or sends a reminder or campaign. This narrows ADR-0007's "no background scheduler" to "no scheduler that acts for students".

## Consequences

- A reminder is no longer missed because the Email page was not opened, as long as the Mac wakes at some point that day.
- ntfy.sh sees class names, the schedule's rhythm and Daniel's task titles. The topic name is the only protection: anyone who learns it can read the digests. A title Daniel types with a student's name in it would leave the Mac; the Add task form says so, and nothing enforces it.
- The LaunchAgent and the topic live outside the repository (the plist names Daniel's folders); NEXT-STEPS records how to install and remove them. A fresh machine has no digest until they are set up.
- While the Mac is shut down or logged out nothing is sent; the login run catches up the same day only.
- A digest sent after Sydney midnight (14:00 to 16:00 Amsterdam) already counts reminder days by Sydney's next date; the last-day line names the weekday of the cut-off so it is never read as a time already past.
- Admin tasks are computed, not stored: a moved class moves its tasks, but a class re-imported under a new id loses its done marks.

## Alternatives rejected

- Writing the dates into Google Calendar: alerts arrive with the Mac off, but cannot know a task is done or give live counts, and need Google OAuth in the backend.
- Pushover: reliable, but paid, with nothing ntfy lacks for one person.
- A Claude cloud routine: it cannot reach a backend that listens on this Mac only without copying student data to the cloud.
- macOS notifications only: Daniel is often away from the Mac.
