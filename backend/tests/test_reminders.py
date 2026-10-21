from datetime import date, datetime
from types import SimpleNamespace as NS

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import reminders as reminders_api
from app.core.database import get_db
from app.models import Class, ClassReminder, EmailCampaign, EmailRecipient
from app.reminders import due_reminders, reminder_date

KUNDALINI = NS(id=1, name="Clearing the Kundalini Channel", start_date=datetime(2026, 10, 31, 14, 0))
APAC_NEW = NS(id=10, first_name="A", last_name="New", tags="SRA", lists="APAC Wizards")
APAC_DONE = NS(id=11, first_name="B", last_name="Done", tags="Clearing Kundalini", lists="APAC Wizards")
NO_FOUNDATIONAL = NS(id=12, first_name="C", last_name="Other", tags="", lists="Global Wizards")


def test_reminder_dates_follow_the_calendar():
    start = date(2026, 11, 11)
    assert reminder_date(start, "2m") == date(2026, 9, 11)
    assert reminder_date(start, "1m") == date(2026, 10, 11)
    assert reminder_date(start, "2w") == date(2026, 10, 28)


def test_month_end_dates_clamp():
    assert reminder_date(date(2027, 3, 31), "1m") == date(2027, 2, 28)


@pytest.mark.parametrize("today, due", [
    (date(2026, 10, 16), False),  # day before the 2-week reminder
    (date(2026, 10, 17), True),   # the day itself
    (date(2026, 10, 24), True),   # 7 days late, last day offered
    (date(2026, 10, 25), False),  # dropped, never sent late
])
def test_grace_window(today, due):
    stages = [r["stage"] for r in due_reminders([KUNDALINI], [], set(), today)]
    assert ("2w" in stages) is due


def test_approved_reminders_are_not_due_again():
    assert due_reminders([KUNDALINI], [], {(1, "2w")}, date(2026, 10, 17)) == []


def test_only_eligible_students_who_have_not_done_the_class():
    [r] = due_reminders([KUNDALINI], [APAC_NEW, APAC_DONE, NO_FOUNDATIONAL], set(), date(2026, 10, 17))
    assert [s.id for s in r["recipients"]] == [10]


def test_classes_off_the_chart_and_past_classes_are_ignored():
    workshop = NS(id=2, name="A workshop not on the chart", start_date=datetime(2026, 10, 31))
    assert due_reminders([workshop], [APAC_NEW], set(), date(2026, 10, 17)) == []
    assert due_reminders([KUNDALINI], [APAC_NEW], set(), date(2026, 10, 31)) == []


@pytest.fixture
def reminders_client(db):
    db.add(Class(id=1, name="Clearing the Kundalini Channel", start_date=datetime(2026, 10, 31, 14, 0)))
    db.commit()
    app = FastAPI()
    app.include_router(reminders_api.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[reminders_api.get_today] = lambda: date(2026, 10, 21)
    return TestClient(app)


def test_due_list_shows_the_late_reminder_with_its_apac_recipients(reminders_client):
    [r] = reminders_client.get("/api/reminders/due").json()
    assert (r["stage"], r["days_late"], r["recipient_count"]) == ("2w", 4, 2)
    assert r["subject"] == "Clearing the Kundalini Channel – 31 October 2026"


def test_approve_records_one_sent_campaign_and_cannot_repeat(reminders_client, db):
    approval = {"class_id": 1, "stage": "2w", "subject": "S", "body": "B"}
    result = reminders_client.post("/api/reminders/approve", json=approval).json()
    assert result["recipients_count"] == 2

    campaign = db.get(EmailCampaign, result["campaign_id"])
    assert (campaign.status, campaign.subject, campaign.recipient_count) == ("sent", "S", 2)
    assert db.query(EmailRecipient).filter_by(campaign_id=campaign.id).count() == 2
    assert db.query(ClassReminder).filter_by(class_id=1, stage="2w").count() == 1

    assert reminders_client.get("/api/reminders/due").json() == []
    assert reminders_client.post("/api/reminders/approve", json=approval).status_code == 409


def test_a_reminder_that_is_not_due_cannot_be_approved(reminders_client):
    approval = {"class_id": 1, "stage": "2m", "subject": "S", "body": "B"}
    assert reminders_client.post("/api/reminders/approve", json=approval).status_code == 404
