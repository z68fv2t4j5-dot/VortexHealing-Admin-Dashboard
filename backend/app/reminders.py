"""Which class reminders are due, and to whom. Timing comes from docs/CLASS_RULES.md
section 3; nothing here sends anything (ADR-0007)."""
from calendar import monthrange
from datetime import date, timedelta
from typing import Iterable

from app.class_rules import class_for, completed_from_tags, is_eligible

# (key, label, how far before the class starts)
STAGES = (("2m", "2 months before", 2), ("1m", "1 month before", 1), ("2w", "2 weeks before", None))
GRACE_DAYS = 7  # a missed reminder stays on the list this long, then is dropped, never sent late


def months_before(d: date, months: int) -> date:
    year, month = divmod(d.year * 12 + d.month - 1 - months, 12)
    return date(year, month + 1, min(d.day, monthrange(year, month + 1)[1]))


def reminder_date(start: date, stage: str) -> date:
    months = next(m for key, _, m in STAGES if key == stage)
    return months_before(start, months) if months else start - timedelta(days=14)


def due_reminders(classes: Iterable, students: Iterable, approved: set, today: date) -> list:
    """Reminders whose date has arrived (within the grace window) and that are not yet approved.

    `classes` have .id, .name and .start_date; `students` are the candidates (the email list),
    with .tags and .lists; `approved` holds (class_id, stage) pairs."""
    students = list(students)
    due = []
    for c in classes:
        cls = class_for(c.name)
        if not cls or not c.start_date:
            continue
        start = c.start_date.date()
        for stage, label, _ in STAGES:
            when = reminder_date(start, stage)
            if (c.id, stage) in approved or not (when <= today <= when + timedelta(days=GRACE_DAYS)) or today >= start:
                continue
            recipients = [s for s in students
                          if cls not in (done := completed_from_tags(s.tags, s.lists)) and is_eligible(cls, done)]
            due.append({"class": c, "stage": stage, "label": label, "reminder_date": when, "recipients": recipients})
    return sorted(due, key=lambda r: (r["reminder_date"], r["class"].start_date))
