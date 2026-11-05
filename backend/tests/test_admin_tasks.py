from datetime import date, datetime
from types import SimpleNamespace as NS

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin_tasks import admin_tasks, quarter_due
from app.api import admin_tasks as admin_api
from app.api import tasks as tasks_api
from app.core.database import get_db
from app.models import AdminTaskDone, Class

FIVE_DAY = NS(id=4, name="Magical Structures", start_date=datetime(2026, 11, 11, 13, 30),
              end_date=datetime(2026, 11, 15, 17, 0))
ONE_DAY = NS(id=6, name="Sensing I", start_date=datetime(2026, 12, 13, 10, 0), end_date=None)
BEFORE_SINCE = NS(id=1, name="Karmic Intensive", start_date=datetime(2026, 10, 30), end_date=datetime(2026, 10, 31))
LATER = date(2027, 6, 30)  # a "today" late enough that every task above is overdue, so listed


def class_dues(classes, today=LATER, done=frozenset()):
    return {t["key"]: t["due"] for t in admin_tasks(classes, set(done), today) if t["key"].startswith("class:")}


def test_class_tasks_count_from_the_start_and_the_end():
    assert class_dues([FIVE_DAY]) == {
        "class:4:prereqs": date(2026, 10, 28),     # 14 days before the start
        "class:4:joining": date(2026, 11, 9),      # 2 days before the start
        "class:4:followup": date(2026, 11, 18),    # 3 days after the end
        "class:4:commission": date(2026, 11, 29),  # 14 days after the end
    }


def test_a_class_without_an_end_date_ends_on_its_start():
    dues = class_dues([ONE_DAY])
    assert (dues["class:6:followup"], dues["class:6:commission"]) == (date(2026, 12, 16), date(2026, 12, 27))


@pytest.mark.parametrize("year, quarter, due", [
    (2027, 1, date(2027, 4, 30)),
    (2027, 2, date(2027, 7, 31)),
    (2027, 3, date(2027, 10, 31)),
    (2026, 4, date(2027, 1, 31)),
])
def test_the_quarterly_task_is_due_the_last_day_of_the_month_after(year, quarter, due):
    assert quarter_due(year, quarter) == due


def test_quarters_start_with_the_one_the_first_digest_falls_in():
    keys = [t["key"] for t in admin_tasks([], set(), date(2027, 4, 30))]
    assert keys == ["quarter:2026Q4:revenue", "quarter:2027Q1:revenue"]


def test_classes_starting_before_the_first_digest_get_no_tasks():
    assert class_dues([BEFORE_SINCE]) == {}


def test_ticked_tasks_are_not_listed():
    assert "class:4:joining" not in class_dues([FIVE_DAY], done={"class:4:joining"})


@pytest.mark.parametrize("today, listed", [
    (date(2026, 11, 1), False),  # 8 days ahead
    (date(2026, 11, 2), True),   # 7 days ahead: coming up
    (date(2026, 11, 9), True),   # the day itself
    (date(2027, 3, 1), True),    # months overdue, still listed until ticked
])
def test_listed_from_seven_days_ahead_until_ticked(today, listed):
    assert ("class:4:joining" in class_dues([FIVE_DAY], today)) is listed


@pytest.fixture
def admin_client(db):
    db.add(Class(id=4, name="Magical Structures", start_date=datetime(2026, 11, 11, 13, 30),
                 end_date=datetime(2026, 11, 15, 17, 0)))
    db.commit()
    app = FastAPI()
    app.include_router(admin_api.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[admin_api.get_today] = lambda: date(2026, 11, 4)
    return TestClient(app)


def test_the_list_shows_overdue_and_coming_up_tasks(admin_client):
    tasks = admin_client.get("/api/admin-tasks").json()
    assert [(t["key"], t["due"], t["days_late"]) for t in tasks] == [
        ("class:4:prereqs", "2026-10-28", 7), ("class:4:joining", "2026-11-09", -5)]


def test_done_is_recorded_once_and_the_task_leaves_the_list(admin_client, db):
    assert admin_client.post("/api/admin-tasks/done", json={"key": "class:4:prereqs"}).status_code == 200
    assert db.query(AdminTaskDone).filter_by(key="class:4:prereqs").count() == 1
    assert [t["key"] for t in admin_client.get("/api/admin-tasks").json()] == ["class:4:joining"]
    assert admin_client.post("/api/admin-tasks/done", json={"key": "class:4:prereqs"}).status_code == 409


def test_a_task_not_on_the_list_cannot_be_ticked(admin_client):
    assert admin_client.post("/api/admin-tasks/done", json={"key": "class:4:commission"}).status_code == 404
    assert admin_client.post("/api/admin-tasks/done", json={"key": "class:99:joining"}).status_code == 404


def test_marking_a_hand_task_done_records_when(db):
    app = FastAPI()
    app.include_router(tasks_api.router, prefix="/api/tasks")
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    task = client.post("/api/tasks/", json={"title": "Order certificates", "due_date": "2026-11-06T00:00:00"}).json()

    done = client.put(f"/api/tasks/{task['id']}", json={"status": "done"}).json()
    assert done["status"] == "done" and done["completed_at"]
    assert client.get(f"/api/tasks/{task['id']}").json()["status"] == "done"
    assert client.put(f"/api/tasks/{task['id']}", json={"status": "finished"}).status_code == 422
