# Plan (feature): a daily push digest of due email reminders and admin tasks
Status: done 2026-11-05 for the code; installed 2026-11-06 on Daniel's go (topic, first real push confirmed on his phone, LaunchAgent). Daniel's answers to the open questions: all three as recommended.
Departures:
- Install, 2026-11-06: the LaunchAgent runs a small script (`~/Library/Application Support/VortexHealing/digest.sh`, the same layout as the load-models login item) rather than the venv's python directly, so that a failing digest sends one "Digest failed" alert a day instead of failing silently. The alert goes through `~/.local/bin/notify`, a command Daniel asked for the same day so that every project, including future ones, can alert him on its own ntfy topic; this digest's topic is registered there too.
- `backend/requirements-test.txt` gained `email-validator==2.1.0` (same pin as `requirements.txt`). The new tasks-router test imports `app/schemas.py`, whose `EmailStr` needs it, and CI installs only that file. Simulating its absence reproduced the `ImportError`.
- The last-day line names the weekday of the cut-off ("approve by Thu 14:00"). A digest sent after Sydney midnight (14:00 to 16:00 Amsterdam) already falls on Sydney's next date, so a bare time read as one already past. The cut-off is 15:00 in the weeks between the two countries' clock changes, not only 14:00 or 16:00.
- `docs/memory/daily-digest.md` and the rebuilt `docs/memory/MEMORY.md` were added by the close routine.

## Investigation

Observed:
- Reminders are worked out only when the Email page is opened (ADR-0007). Each is offered for 7 days, then dropped. On 2026-11-04 the Magical Structures 2-week reminder (34 eligible) was on its last day and another was on day 6; neither had been seen. That is the cost ADR-0007 names, measured.
- `class_reminders` is empty: no reminder has been approved through the dashboard yet.
- All 24 upcoming classes have a start and an end date, and all 24 are Daniel's.
- No admin-task timing is recorded anywhere. The `tasks` table holds one task, with no due date. The Tasks page can only create tasks through Qwen ("AI Task"), shows no Done control, and `PUT /api/tasks/{id}` never sets `completed_at`.
- The Mac's time zone is Europe/Amsterdam. Reminder dates are Sydney dates (`get_today()` in `app/api/reminders.py`).
- A LaunchAgent already runs on this Mac for the dashboard (`com.vortexhealing.load-models`, outside the repository), so the pattern is known.
- `create_all` creates missing tables but never alters existing ones; new tables are safe, a new column on `tasks` is not.

Daniel's answers (interview, 2026-11-04):
- Channel: the ntfy phone app, on a private topic at ntfy.sh. No student names in any push.
- One digest a day at 09:00 Amsterdam time. If the Mac is asleep or off, send when it wakes, the same Amsterdam day; never two a day; silent when nothing is due.
- Content: due today, overdue, then "coming up" for the next 7 days.
- Email reminders: nudge on the day one falls due, 3 days later, and on its last day (7 days after), which says it is the last day.
- Admin tasks, per class: check enrolled students' prerequisites 14 days before the start; send joining details 2 days before the start; follow-up email to attendees 3 days after the end; commission form 14 days after the end. Revenue and expenses quarterly, due the last day of the month after each quarter (31 Jan, 30 Apr, 31 Jul, 31 Oct), with a heads-up 7 days before. Hand-added tasks by their due date.
- Overdue admin tasks repeat in every digest until ticked done.

Assumed:
- Every class in the `classes` table is one Daniel runs, so every class gets the four class tasks.
- "Done" for an email reminder is its approval on the Email page; nothing new is needed for that.
- The Mac stays logged in to Daniel's account; a LaunchAgent does not run while it is logged out or shut down.

## Acceptance criteria

1. Once per Amsterdam day, at the first hourly run at or after 09:00 Amsterdam time, Daniel's phone receives one ntfy notification. It lists what is due today, what is overdue, and what is coming up in the next 7 days. If nothing is due today or overdue, nothing is sent that day.
2. If the Mac was asleep at 09:00, the digest arrives when it wakes, the same Amsterdam day. If the push fails (no network), the next hourly run tries again. There is never a second digest the same day.
3. An unapproved email reminder appears under "today" on the day it falls due, 3 days later and 7 days later, with its stage and eligible count. The day-7 line gives the Amsterdam time it closes (Sydney midnight: 14:00 in the northern winter, 16:00 in summer). Once approved, it no longer appears.
4. The Tasks page lists the class admin tasks and the quarterly task that are overdue or due in the next 7 days, each with a Done button. A ticked task leaves the page and every later digest. Until it is ticked, an overdue task appears in every digest.
5. The Tasks page can add a task with a title and a due date (no Qwen needed), and mark any task done. Hand-added tasks follow the same rules as admin tasks in the digest.
6. No push carries a student's name, email address or eligibility list. It carries class names, counts and Daniel's own task titles only.
7. Nothing about the email flow changes: no reminder is approved, recorded or sent by the scheduled job.

Surface: backend/app/admin_tasks.py (new), backend/app/digest.py (new), backend/app/api/admin_tasks.py (new), backend/app/api/reminders.py (the due helper made public for the digest), backend/app/api/tasks.py (Done sets `completed_at`), backend/app/models.py (new tables `admin_tasks_done` and `digest_log`), backend/app/core/config.py (`NTFY_SERVER`, `NTFY_TOPIC`), backend/.env.example, backend/main.py (mount the router), backend/tests/test_admin_tasks.py (new), backend/tests/test_digest.py (new), frontend/src/components/AdminTasksDue.tsx (new), frontend/src/pages/Tasks.tsx (render it; Add task; Done), docs/CLASS_RULES.md (admin task timing), docs/ARCHITECTURE.md, docs/adr/0010-daily-digest-to-daniel.md (new), docs/adr/0007-reminders-computed-on-view.md (status line only), docs/adr/README.md, NEXT-STEPS.md, docs/sessions/session_<stamp>.md, this plan.

Outside the repository, on Daniel's Mac and only with his go: `~/Library/LaunchAgents/com.vortexhealing.digest.plist`, and `NTFY_TOPIC` in `backend/.env`.

## Design

- **Two clocks.** Email reminders keep the Sydney date (they are computed exactly as the Email page computes them). Admin tasks, hand-added tasks and the 09:00 decision use the Amsterdam date. Both come from `zoneinfo`, standard library.
- `admin_tasks.py`: the four class tasks as data (`key`, title, counted from the start or the end, days offset), plus the quarterly task, and one pure function `admin_tasks(classes, done_keys, today, horizon=7)` that returns the not-done tasks that are overdue or due within the horizon. A one-day class's end is its start. Tasks exist only for classes starting on or after `SINCE = 2026-11-04` and quarters ending on or after it, so the first digest is not a backlog of every past class. Pure so it is tested without a database or a clock, like `due_reminders`.
  - Justified: computed on view like reminders (ADR-0007's pattern), so a moved class date moves its tasks and there are no stale rows to clean up.
- New table `admin_tasks_done` (`key` unique, `done_at`). Keys are `class:<id>:<kind>` and `quarter:<yyyy>Q<n>:revenue`. Justified: the done marks need to persist, and a new table needs no rebuild of `tasks`.
- New table `digest_log` (`day` unique, Amsterdam date; `sent_at`; `lines`). Justified: it is how "once a day" survives hourly runs and restarts. A row is written when the digest is sent, or when the day had nothing due; a failed push writes nothing, so the next hour retries.
- `digest.py`:
  - `build(reminders_due, reminders_upcoming, admin_items, hand_tasks, today_syd, today_ams)` returns `None` or a title and body. Pure. Email nudges on days 0, 3 and 7 of the window; the day-7 line converts Sydney midnight to Amsterdam time. The quarterly task gets a heads-up line in "today" exactly 7 days before its due date. "Coming up" lists new reminder dates and task due dates in the next 7 days. The title reads, for example, "VH admin: 1 due today, 1 overdue".
  - `should_send(now_ams, logged_today)`: true from 09:00 Amsterdam if the day has no log row. Pure.
  - `send(title, body)`: one JSON POST to `NTFY_SERVER` with `topic`, `title`, `message`, using `urllib.request` from the standard library (no new dependency). JSON rather than headers, because class names hold non-ASCII characters. Refuses to run without `NTFY_TOPIC`. A non-2xx answer raises an error.
  - `python -m app.digest [--dry-run]`: opens the database with the app's own session, creates missing tables, decides, builds, sends, logs. `--dry-run` prints the message and neither sends nor logs.
  - It reads students only through the same due helper the Email page uses, and passes on counts, never names.
- `app/api/admin_tasks.py`: `GET /api/admin-tasks` (overdue and next 7 days) and `POST /api/admin-tasks/done` `{key}` (404 when the key is not a current task, 409 when already done).
- `app/api/tasks.py`: setting status to done stores `TaskStatus.DONE` and sets `completed_at`.
- `AdminTasksDue.tsx`: a list at the top of the Tasks page, overdue items marked, a Done button each. It is in `components/` like `RemindersDue.tsx`. `Tasks.tsx` gains an "Add task" modal (title and date, in the existing modal pattern) with a one-line hint that titles reach the phone through ntfy.sh, plus a Done button on open tasks.
- **Scheduling, outside the repository.** A LaunchAgent runs `backend/venv/bin/python -m app.digest` with `WorkingDirectory` set to `backend/`, at minute 0 of every hour (`StartCalendarInterval`) and at login (`RunAtLoad`), logging to `~/Library/Logs/vortexhealing-digest.log`. launchd runs a calendar job missed during sleep once on wake, which gives the catch-up. The plist names Daniel's folders, so it is not committed (Part A section 5); NEXT-STEPS records how to install and remove it, as for the model loader.
- **Topic.** `NTFY_TOPIC` is a random 24-character string written into `backend/.env` without being printed. Daniel copies it from that file into the ntfy app. It is the only secret: anyone who knows it can read the digests.

Test plan:
- Unit, `admin_tasks` (synthetic classes): each class task's due date (start minus 14, start minus 2, end plus 3, end plus 14); a one-day class uses its start as its end; quarterly due dates, including Q1 to 30 April and Q4 to 31 January of the next year; done keys excluded; classes and quarters before `SINCE` excluded; overdue tasks kept with no limit, upcoming limited to 7 days.
- Unit, `digest.build`: nudges on days 0, 3 and 7 and on no other day; the day-7 cut-off reads 14:00 in a January week and 16:00 in a June week; overdue admin and hand-added tasks listed every day; the quarterly heads-up exactly 7 days before; nothing due today or overdue gives `None`; "coming up" stops at 7 days; synthetic students named in the input never appear in the output.
- Unit, `should_send`: before 09:00 Amsterdam, no; at 09:00 and after, yes; already logged, no; a "now" given in Sydney time is still judged in Amsterdam time.
- Unit, the CLI with the sender replaced: a failed send writes no log row; a sent digest writes one; a nothing-due day writes one and sends nothing; `--dry-run` sends and writes nothing; no `NTFY_TOPIC`, no send. The POST body has `topic`, `title` and `message`.
- API: `GET /api/admin-tasks` lists due items; `POST /api/admin-tasks/done` records once, then 409, and 404 for an unknown key; the item then leaves the list. `PUT /api/tasks/{id}` with status done sets `completed_at` and reads back as done.
- Each new test is seen red once by breaking the behaviour it names.
- E2E: n/a, the frontend has no test runner. Manual: the Tasks page in the browser (Done, Add task, a clean console, a phone-width window). One real push to Daniel's phone with his go, then one LaunchAgent run seen in its log.

Architecture map delta: yes. New layout rows (`admin_tasks.py`, `digest.py`, `AdminTasksDue.tsx`) and a new flow 8 (digest). The invariant "No reminder is recorded without a person's click, and none twice. There is no background scheduler" becomes "... The only scheduled job, the digest, writes `digest_log` alone and never approves or records a reminder", with `verify: absent 'ClassReminder\(|EmailCampaign\(|EmailRecipient\(' in backend/app/digest.py`. New invariant: pushes carry no student data, with `verify: absent 'first_name|last_name|\.email\b' in backend/app/digest.py`.

ADR: yes, 0010. It narrows ADR-0007's "no background scheduler" to "no scheduler that acts for students". It also records ntfy.sh as a new outside destination for class names, counts and Daniel's task titles, and why Google Calendar, Pushover, a cloud routine and Mac-only notifications were rejected. ADR-0007's status line gains "narrowed by 0010".

Cross-repo impact: none.

## Open questions

1. Should hand-added task titles go into the push as written? [Recommended: yes, with the hint on the Add task form. A digest that says only "1 task due" is not useful, and Daniel writes the titles. If a title could hold a student's name, choose counts only instead.]
2. Should tasks start from classes beginning on or after 4 November 2026 and quarters ending after it? [Recommended: yes. The first digest then shows the Magical Structures prerequisite check (due 28 October) as overdue, and treats Q3 2026 revenue and expenses (due 31 October) as done.]
3. Should a Done click be final in this change? [Recommended: yes. Undo is a BACKLOG line, because a mis-tick is rare and can be removed from `admin_tasks_done` by hand.]

## BACKLOG

- Undo for a Done click (admin and hand-added tasks).
- The Tasks page cannot edit or delete a task.
- Reseeding classes (the open `seed_classes.py` prerequisites thread) may change class ids, orphaning `admin_tasks_done` and `class_reminders` rows. Check this before reseeding.
