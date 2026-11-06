import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace as NS
from zoneinfo import ZoneInfo

import pytest

from app import digest
from app.digest import build, closes_at, hand_tasks, run, should_send, upcoming_reminders
from app.models import Class, DigestLog, TaskStatus

AMS, SYD = ZoneInfo("Europe/Amsterdam"), ZoneInfo("Australia/Sydney")
MS = NS(id=4, name="Magical Structures", start_date=datetime(2026, 11, 11, 13, 30))
NAMED = [NS(first_name="Zelda", last_name="Quorn", email="zq@example.com"),
         NS(first_name="Yuri", last_name="Pell", email="yp@example.com")]
REMINDER = {"class": MS, "stage": "2w", "label": "2 weeks before", "reminder_date": date(2026, 10, 28),
            "recipients": NAMED}
TODAY = date(2026, 11, 4)
NOW = datetime(2026, 11, 4, 9, 5, tzinfo=AMS)


def task(title, due, kind="hand"):
    return {"title": title, "due": due, "kind": kind}


@pytest.mark.parametrize("late", range(8))
def test_email_reminders_are_pushed_on_days_0_3_and_7_only(late):
    today = REMINDER["reminder_date"] + timedelta(days=late)
    assert (build([REMINDER], [], [], today, today) is not None) is (late in (0, 3, 7))


def test_the_last_day_says_when_the_reminder_closes():
    title, body = build([REMINDER], [], [], TODAY, TODAY)
    assert title == "VH admin: 1 due today"
    assert body == "TODAY\n• Email Magical Structures, 2 weeks before (2 eligible). Last day: approve by Wed 14:00"


def test_the_close_time_follows_both_clocks():
    assert closes_at(date(2027, 1, 5)) == "Tue 14:00"  # northern winter, Sydney summer
    assert closes_at(date(2027, 6, 1)) == "Tue 16:00"  # northern summer, Sydney winter
    assert closes_at(date(2026, 9, 27)) == "Sun 15:00"  # last day 4 Oct: Sydney's summer time began that day, Amsterdam's still on


def test_no_student_name_or_address_reaches_the_push():
    title, body = build([REMINDER], [], [], date(2026, 10, 28), date(2026, 10, 28))
    for s in NAMED:
        for value in (s.first_name, s.last_name, s.email):
            assert value not in title + body


def test_overdue_tasks_are_listed_every_day_until_done():
    tasks = [task("Check enrolled students' prerequisites: Magical Structures", date(2026, 10, 28), "prereqs")]
    for day in (TODAY, date(2026, 11, 20)):
        title, body = build([], [], tasks, day, day)
        assert title == "VH admin: 1 overdue"
        assert body == "OVERDUE\n• Check enrolled students' prerequisites: Magical Structures (due Wed 28 Oct)"


def test_a_task_due_today_is_under_today():
    tasks = [task("Send joining details: Magical Structures", date(2026, 11, 9), "joining")]
    assert build([], [], tasks, date(2026, 11, 9), date(2026, 11, 9))[1] == \
        "TODAY\n• Send joining details: Magical Structures"


def test_a_day_with_nothing_due_or_overdue_is_silent():
    tasks = [task("Send joining details: Magical Structures", date(2026, 11, 9), "joining")]
    assert build([], [], tasks, TODAY, TODAY) is None


def test_the_quarterly_task_gets_a_heads_up_seven_days_before():
    tasks = [task("Revenue and expenses, Q4 2026", date(2027, 1, 31), "revenue")]
    assert build([], [], tasks, date(2027, 1, 23), date(2027, 1, 23)) is None
    assert build([], [], tasks, date(2027, 1, 24), date(2027, 1, 24))[1] == \
        "TODAY\n• Heads-up: Revenue and expenses, Q4 2026 is due Sun 31 Jan"
    assert build([], [], tasks, date(2027, 1, 25), date(2027, 1, 25)) is None


def test_coming_up_follows_what_is_due():
    tasks = [task("Overdue thing", date(2026, 11, 1)),
             task("Send joining details: Magical Structures", date(2026, 11, 9), "joining")]
    coming = [{"class": NS(id=7, name="Karmic Intensive"), "stage": "2m", "label": "2 months before",
               "reminder_date": date(2026, 11, 9)}]
    title, body = build([], coming, tasks, TODAY, TODAY)
    assert body == ("OVERDUE\n• Overdue thing (due Sun 1 Nov)\n\n"
                    "COMING UP\n• Mon 9 Nov: Send joining details: Magical Structures\n"
                    "• Mon 9 Nov: Email Karmic Intensive, 2 months before")


def test_upcoming_reminders_look_seven_days_ahead():
    karmic = NS(id=7, name="Karmic Intensive", start_date=datetime(2027, 1, 9, 9, 0))  # 2-month notice 9 Nov
    assert [r["stage"] for r in upcoming_reminders([karmic], set(), date(2026, 11, 2))] == ["2m"]
    assert upcoming_reminders([karmic], set(), date(2026, 11, 1)) == []  # 8 days ahead
    assert upcoming_reminders([karmic], set(), date(2026, 11, 9)) == []  # due today: the due list has it
    assert upcoming_reminders([karmic], {(7, "2m")}, date(2026, 11, 2)) == []
    workshop = NS(id=8, name="A workshop not on the chart", start_date=datetime(2027, 1, 9))
    assert upcoming_reminders([workshop], set(), date(2026, 11, 2)) == []


def test_a_long_coming_up_list_is_cut():
    tasks = [task("Overdue thing", date(2026, 11, 1))] + [task(f"Task {n}", date(2026, 11, 6)) for n in range(12)]
    body = build([], [], tasks, TODAY, TODAY)[1]
    assert body.count("\n• Fri 6 Nov: ") == 10 and body.endswith("\n• and 2 more")


def test_hand_tasks_need_a_due_date_and_not_done():
    rows = [NS(title="A", due_date=datetime(2026, 11, 11), status=TaskStatus.TODO),
            NS(title="B", due_date=datetime(2026, 11, 12), status=TaskStatus.TODO),  # 8 days ahead
            NS(title="C", due_date=datetime(2026, 10, 1), status=TaskStatus.DONE),
            NS(title="D", due_date=None, status=TaskStatus.TODO)]
    assert [t["title"] for t in hand_tasks(rows, TODAY)] == ["A"]


@pytest.mark.parametrize("now, logged, send", [
    (datetime(2026, 11, 4, 8, 59, tzinfo=AMS), False, False),
    (datetime(2026, 11, 4, 9, 0, tzinfo=AMS), False, True),
    (datetime(2026, 11, 4, 16, 30, tzinfo=AMS), False, True),  # the Mac woke late
    (datetime(2026, 11, 4, 9, 0, tzinfo=AMS), True, False),
    (datetime(2026, 11, 4, 18, 30, tzinfo=SYD), False, False),  # 08:30 in Amsterdam
    (datetime(2026, 11, 4, 19, 0, tzinfo=SYD), False, True),    # 09:00 in Amsterdam
])
def test_send_from_nine_amsterdam_time_once_a_day(now, logged, send):
    assert should_send(now, logged) is send


@pytest.fixture
def due_db(db):
    db.add(Class(id=4, name="Magical Structures", start_date=datetime(2026, 11, 11, 13, 30),
                 end_date=datetime(2026, 11, 15, 17, 0)))
    db.commit()
    return db


def test_a_digest_is_sent_once_and_logged(due_db):
    sent = []
    assert run(due_db, NOW, lambda title, body: sent.append(body)).startswith("sent")
    assert run(due_db, NOW + timedelta(hours=1), lambda title, body: sent.append(body)) is None
    assert len(sent) == 1 and due_db.query(DigestLog).count() == 1
    assert "Last day: approve by Wed 14:00" in sent[0] and "Check enrolled students' prerequisites" in sent[0]


def test_a_failed_send_logs_nothing_so_the_next_hour_retries(due_db):
    def offline(title, body):
        raise OSError("no network")
    with pytest.raises(OSError):
        run(due_db, NOW, offline)
    due_db.rollback()
    assert due_db.query(DigestLog).count() == 0
    sent = []
    run(due_db, NOW + timedelta(hours=1), lambda title, body: sent.append(body))
    assert len(sent) == 1


def test_a_day_with_nothing_due_is_logged_and_sends_nothing(db):
    sent = []
    assert run(db, NOW, lambda title, body: sent.append(body)) == "nothing due"
    assert sent == [] and db.query(DigestLog).filter_by(day=TODAY).one().lines == 0


def test_nothing_happens_before_nine(due_db):
    assert run(due_db, NOW.replace(hour=8), lambda title, body: pytest.fail("sent")) is None
    assert due_db.query(DigestLog).count() == 0


def test_a_dry_run_sends_and_logs_nothing(due_db):
    out = run(due_db, NOW.replace(hour=7), lambda title, body: pytest.fail("sent"), dry_run=True)
    assert out.startswith("VH admin: ") and due_db.query(DigestLog).count() == 0


def test_send_publishes_one_json_message(monkeypatch):
    seen = {}

    class Response:
        def close(self):
            pass

    def fake_urlopen(request, timeout):
        seen.update(url=request.full_url, method=request.get_method(), body=json.loads(request.data))
        return Response()

    monkeypatch.setattr(digest.urllib.request, "urlopen", fake_urlopen)
    digest.send("T", "Email Merlin’s Jewel", "https://ntfy.example/", "topic-123")
    assert seen == {"url": "https://ntfy.example", "method": "POST",
                    "body": {"topic": "topic-123", "title": "T", "message": "Email Merlin’s Jewel", "tags": ["bell"]}}


def test_no_topic_means_no_send(monkeypatch):
    monkeypatch.setattr(digest.settings, "NTFY_TOPIC", None)
    assert digest.main([]) == 2


def test_the_command_reports_what_happened(monkeypatch, capsys):
    monkeypatch.setattr(digest.settings, "NTFY_TOPIC", "topic-123")
    monkeypatch.setattr(digest, "run", lambda db, now, sender, dry_run: "sent, 2 line(s)")
    assert digest.main([]) == 0
    assert capsys.readouterr().out.strip().endswith("sent, 2 line(s)")


def test_a_failed_run_exits_non_zero_for_the_log(monkeypatch, capsys):
    def offline(db, now, sender, dry_run):
        raise OSError("no network")
    monkeypatch.setattr(digest.settings, "NTFY_TOPIC", "topic-123")
    monkeypatch.setattr(digest, "run", offline)
    assert digest.main([]) == 1
    assert "failed: no network" in capsys.readouterr().err


def test_a_dry_run_needs_no_topic(monkeypatch, capsys):
    monkeypatch.setattr(digest.settings, "NTFY_TOPIC", None)
    assert digest.main(["--dry-run"]) == 0  # the test database is empty and in memory
    assert capsys.readouterr().out.strip()
