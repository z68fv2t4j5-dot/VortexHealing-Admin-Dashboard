---
name: daily-digest
description: Daily ntfy push of due reminders and admin tasks via python -m app.digest, run hourly by a LaunchAgent outside the repo; design in ADR-0010
metadata:
  type: project
---

**Fact:** `cd backend && python -m app.digest [--dry-run]` sends one push a day from 09:00 Amsterdam time; `digest_log` stops repeats. The LaunchAgent and `NTFY_TOPIC` live on Daniel's Mac, not here. Admin-task timing is in `docs/CLASS_RULES.md` section 5.

**Why:** reminders only showed when the Email page was opened, so a week away missed them.

**Authority:** ADR-0010
