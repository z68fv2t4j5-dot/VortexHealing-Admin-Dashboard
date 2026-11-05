"""The daily push digest (ADR-0010): email reminders and admin tasks that are due, once a day from
09:00 Amsterdam time, to Daniel's phone through ntfy. It reads; it never approves, records or sends email.
A LaunchAgent runs it every hour: `cd backend && python -m app.digest [--dry-run]`."""
import argparse
import json
import sys
import urllib.request
from datetime import date, datetime, time, timedelta
from typing import Callable, Iterable, Optional
from zoneinfo import ZoneInfo

from app.admin_tasks import HORIZON_DAYS, admin_tasks
from app.api.reminders import due_now
from app.class_rules import class_for
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import AdminTaskDone, Class, ClassReminder, DigestLog, Task, TaskStatus
from app.reminders import GRACE_DAYS, STAGES, reminder_date

AMSTERDAM = ZoneInfo("Europe/Amsterdam")
SYDNEY = ZoneInfo("Australia/Sydney")
SEND_HOUR = 9  # Amsterdam time
NUDGE_DAYS = (0, 3, GRACE_DAYS)  # an unapproved reminder is pushed on its day, 3 days on, and on its last day
HEADS_UP_DAYS = 7  # the quarterly task is announced this many days before it is due
MAX_COMING = 10  # a longer "coming up" list is cut, so the digest stays one short message


def should_send(now: datetime, logged_today: bool) -> bool:
    """From 09:00 Amsterdam time, once per Amsterdam day, wherever the Mac's clock is set"""
    return not logged_today and now.astimezone(AMSTERDAM).hour >= SEND_HOUR


def closes_at(reminder_day: date) -> str:
    """When a reminder's last day ends, in Amsterdam: Sydney midnight, 14:00 to 16:00 by season. The
    weekday is named because a digest sent late in the day already falls on Sydney's next date."""
    end = datetime.combine(reminder_day + timedelta(days=GRACE_DAYS + 1), time(0), SYDNEY)
    return f"{end.astimezone(AMSTERDAM):%a %H:%M}"


def _day(d: date) -> str:
    return f"{d:%a} {d.day} {d:%b}"


def upcoming_reminders(classes: Iterable, approved: set, today: date, horizon: int = HORIZON_DAYS) -> list:
    """Reminders whose date falls in the next `horizon` days (Sydney dates); not yet on the due list"""
    out = []
    for c in classes:
        if not class_for(c.name) or not c.start_date:
            continue
        for stage, label, _ in STAGES:
            when = reminder_date(c.start_date.date(), stage)
            if (c.id, stage) not in approved and today < when <= today + timedelta(days=horizon):
                out.append({"class": c, "stage": stage, "label": label, "reminder_date": when})
    return out


def hand_tasks(tasks: Iterable, today: date, horizon: int = HORIZON_DAYS) -> list:
    """Tasks from the Tasks page with a due date, not done, overdue or due within `horizon` days"""
    last = today + timedelta(days=horizon)
    return [{"title": t.title, "due": t.due_date.date(), "kind": "hand"} for t in tasks
            if t.due_date and t.status != TaskStatus.DONE and t.due_date.date() <= last]


def build(reminders_due: list, reminders_coming: list, tasks: list, today_syd: date, today_ams: date) -> Optional[tuple]:
    """The digest's title and body, or None on a day with nothing due today and nothing overdue.

    Reminders are `due_reminders` dicts on Sydney dates; only their recipient count is used, never a
    name. `tasks` are admin and hand-added tasks with a title and an Amsterdam due date."""
    today, overdue, coming = [], [], []
    for r in reminders_due:
        late = (today_syd - r["reminder_date"]).days
        if late in NUDGE_DAYS:
            line = f"Email {r['class'].name}, {r['label']} ({len(r['recipients'])} eligible)"
            if late == GRACE_DAYS:
                line += f". Last day: approve by {closes_at(r['reminder_date'])}"
            today.append(line)
    for t in sorted(tasks, key=lambda t: t["due"]):
        days = (t["due"] - today_ams).days
        if days < 0:
            overdue.append(f"{t['title']} (due {_day(t['due'])})")
        elif days == 0:
            today.append(t["title"])
        elif t["kind"] == "revenue" and days == HEADS_UP_DAYS:
            today.append(f"Heads-up: {t['title']} is due {_day(t['due'])}")
        else:
            coming.append((t["due"], t["title"]))
    if not today and not overdue:
        return None
    coming += [(r["reminder_date"], f"Email {r['class'].name}, {r['label']}") for r in reminders_coming]
    coming.sort(key=lambda c: c[0])
    later = [f"{_day(d)}: {text}" for d, text in coming[:MAX_COMING]]
    if len(coming) > MAX_COMING:
        later.append(f"and {len(coming) - MAX_COMING} more")
    counts = [f"{n} {what}" for n, what in ((len(today), "due today"), (len(overdue), "overdue")) if n]
    sections = (("TODAY", today), ("OVERDUE", overdue), ("COMING UP", later))
    body = "\n\n".join(head + "".join(f"\n• {line}" for line in lines) for head, lines in sections if lines)
    return "VH admin: " + ", ".join(counts), body


def collect(db, now: datetime) -> tuple:
    """Everything `build` needs, read the way the Email and Tasks pages read it"""
    today_syd, today_ams = now.astimezone(SYDNEY).date(), now.astimezone(AMSTERDAM).date()
    classes = db.query(Class).all()
    approved = {(r.class_id, r.stage) for r in db.query(ClassReminder).all()}
    done = {d.key for d in db.query(AdminTaskDone).all()}
    tasks = admin_tasks(classes, done, today_ams) + hand_tasks(db.query(Task).all(), today_ams)
    return due_now(db, today_syd), upcoming_reminders(classes, approved, today_syd), tasks, today_syd, today_ams


def send(title: str, body: str, server: str, topic: str) -> None:
    """One ntfy message, published as JSON because class names are not safe in HTTP headers; raises on failure"""
    payload = json.dumps({"topic": topic, "title": title, "message": body, "tags": ["bell"]}).encode()
    request = urllib.request.Request(server.rstrip("/"), data=payload, method="POST",
                                     headers={"Content-Type": "application/json"})
    urllib.request.urlopen(request, timeout=15).close()


def run(db, now: datetime, sender: Callable[[str, str], None], dry_run: bool = False) -> Optional[str]:
    """Decide, build, send and log, at most once per Amsterdam day. Returns what happened, or None when
    it is not time yet. A failed send raises before anything is logged, so the next hourly run retries."""
    if dry_run:
        digest = build(*collect(db, now))
        return "\n\n".join(digest) if digest else "nothing due"
    day = now.astimezone(AMSTERDAM).date()
    if not should_send(now, db.query(DigestLog).filter_by(day=day).first() is not None):
        return None
    digest = build(*collect(db, now))
    if digest:
        sender(*digest)
    lines = digest[1].count("\n• ") if digest else 0
    db.add(DigestLog(day=day, lines=lines))
    db.commit()
    return f"sent, {lines} line(s)" if digest else "nothing due"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.digest", description="The daily push digest (ADR-0010).")
    parser.add_argument("--dry-run", action="store_true", help="print today's digest; send and record nothing")
    args = parser.parse_args(argv)
    if not args.dry_run and not settings.NTFY_TOPIC:
        print("NTFY_TOPIC is not set in backend/.env; nothing sent", file=sys.stderr)
        return 2
    Base.metadata.create_all(bind=engine)  # the digest may run before the backend has made its new tables
    db = SessionLocal()
    stamp = f"{datetime.now(AMSTERDAM):%Y-%m-%d %H:%M}"
    try:
        result = run(db, datetime.now(AMSTERDAM),
                     lambda title, body: send(title, body, settings.NTFY_SERVER, settings.NTFY_TOPIC), args.dry_run)
    except Exception as e:  # logged by the LaunchAgent; the next hour tries again
        db.rollback()
        print(f"{stamp} failed: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()
    if result:
        print(result if args.dry_run else f"{stamp} {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
