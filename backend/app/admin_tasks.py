"""Admin tasks worked out from the class schedule, plus the quarterly revenue and expenses task.
Timing comes from docs/CLASS_RULES.md section 5. A ticked task is its key in `admin_tasks_done`."""
from calendar import monthrange
from datetime import date, timedelta
from typing import Iterable

# (kind, title, counted from the class's "start" or "end", days after that date; negative is before)
CLASS_TASKS = (
    ("prereqs", "Check enrolled students' prerequisites", "start", -14),
    ("joining", "Send joining details", "start", -2),
    ("followup", "Follow-up email to attendees", "end", 3),
    ("commission", "Commission form", "end", 14),
)
QUARTERLY_TITLE = "Revenue and expenses"
SINCE = date(2026, 11, 4)  # the first digest; classes starting and quarters ending before it get no tasks
HORIZON_DAYS = 7  # how far ahead "coming up" looks


def quarter_due(year: int, quarter: int) -> date:
    """The last day of the month after the quarter: Q1 is due 30 April, Q4 on 31 January the next year"""
    year, month = (year + 1, 1) if quarter == 4 else (year, quarter * 3 + 1)
    return date(year, month, monthrange(year, month)[1])


def _all_tasks(classes: Iterable, last: date) -> list:
    tasks = []
    for c in classes:
        if not c.start_date or c.start_date.date() < SINCE:
            continue
        start = c.start_date.date()
        end = c.end_date.date() if c.end_date else start
        for kind, title, anchor, days in CLASS_TASKS:
            due = (start if anchor == "start" else end) + timedelta(days=days)
            tasks.append({"key": f"class:{c.id}:{kind}", "title": f"{title}: {c.name}", "due": due, "kind": kind})
    year, quarter = SINCE.year, (SINCE.month - 1) // 3 + 1  # the quarter SINCE falls in ends after it
    while (due := quarter_due(year, quarter)) <= last:
        tasks.append({"key": f"quarter:{year}Q{quarter}:revenue", "title": f"{QUARTERLY_TITLE}, Q{quarter} {year}",
                      "due": due, "kind": "revenue"})
        year, quarter = (year + 1, 1) if quarter == 4 else (year, quarter + 1)
    return tasks


def admin_tasks(classes: Iterable, done_keys: set, today: date, horizon: int = HORIZON_DAYS) -> list:
    """Tasks not yet ticked that are overdue (however long) or due within `horizon` days, earliest first.

    `classes` have .id, .name, .start_date and .end_date; dates are Daniel's (Amsterdam) dates."""
    last = today + timedelta(days=horizon)
    due = [t for t in _all_tasks(classes, last) if t["key"] not in done_keys and t["due"] <= last]
    return sorted(due, key=lambda t: (t["due"], t["title"]))
