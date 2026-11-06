from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.admin_tasks import admin_tasks
from app.core.database import get_db
from app.models import AdminTaskDone, Class

router = APIRouter()


def get_today() -> date:
    """Admin tasks follow Daniel's date, in Amsterdam (docs/CLASS_RULES.md section 5); tests override this"""
    return datetime.now(ZoneInfo("Europe/Amsterdam")).date()


class TaskDone(BaseModel):
    key: str


def due_now(db: Session, today: date) -> list:
    done = {d.key for d in db.query(AdminTaskDone).all()}
    return admin_tasks(db.query(Class).all(), done, today)


@router.get("/admin-tasks")
async def list_due(db: Session = Depends(get_db), today: date = Depends(get_today)):
    """Class and quarterly tasks that are overdue or due in the next 7 days"""
    return [{"key": t["key"], "title": t["title"], "due": t["due"].isoformat(), "days_late": (today - t["due"]).days}
            for t in due_now(db, today)]


@router.post("/admin-tasks/done")
async def mark_done(done: TaskDone, db: Session = Depends(get_db), today: date = Depends(get_today)):
    """Tick a listed task; it leaves the Tasks page and every later digest"""
    if db.query(AdminTaskDone).filter_by(key=done.key).first():
        raise HTTPException(status_code=409, detail="This task is already done")
    if not any(t["key"] == done.key for t in due_now(db, today)):
        raise HTTPException(status_code=404, detail="This task is not on the list")
    db.add(AdminTaskDone(key=done.key))
    try:
        db.commit()
    except IntegrityError:  # ticked twice at the same moment
        db.rollback()
        raise HTTPException(status_code=409, detail="This task is already done")
    return {"key": done.key}
