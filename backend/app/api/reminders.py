from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.email_campaigns import EMAIL_LIST, filter_students_by_tags_and_lists
from app.core.database import get_db
from app.models import Class, ClassReminder, EmailCampaign, EmailRecipient
from app.reminders import due_reminders

router = APIRouter()


def get_today() -> date:
    """Reminder dates are Sydney dates (docs/CLASS_RULES.md section 3); tests override this"""
    return datetime.now(ZoneInfo("Australia/Sydney")).date()


class ReminderApproval(BaseModel):
    class_id: int
    stage: str
    subject: str
    body: str


def _due(db: Session, today: date) -> list:
    approved = {(r.class_id, r.stage) for r in db.query(ClassReminder).all()}
    students = filter_students_by_tags_and_lists(db, "", EMAIL_LIST)
    return due_reminders(db.query(Class).all(), students, approved, today)


def _default_text(name: str, start: datetime) -> tuple:
    when = f"{start.day} {start:%B %Y}"
    subject = f"{name} – {when}"
    body = (f"Dear VortexHealing student,\n\n{name} begins on {when}. "
            "Based on the classes you have completed, you are eligible to join.\n\n"
            "[Add registration link and details]\n\nWarm regards,\nDaniel")
    return subject, body


@router.get("/reminders/due")
async def list_due(db: Session = Depends(get_db), today: date = Depends(get_today)):
    """Reminders waiting for approval, with pre-filled text and sample recipients"""
    out = []
    for r in _due(db, today):
        c = r["class"]
        subject, body = _default_text(c.name, c.start_date)
        out.append({
            "class_id": c.id,
            "class_name": c.name,
            "class_date": c.start_date.date().isoformat(),
            "stage": r["stage"],
            "label": r["label"],
            "reminder_date": r["reminder_date"].isoformat(),
            "days_late": (today - r["reminder_date"]).days,
            "recipient_count": len(r["recipients"]),
            "sample_recipients": [f"{s.first_name} {s.last_name}".strip() for s in r["recipients"][:5]],
            "subject": subject,
            "body": body,
        })
    return out


@router.post("/reminders/approve")
async def approve(approval: ReminderApproval, db: Session = Depends(get_db), today: date = Depends(get_today)):
    """Record a due reminder as sent to everyone eligible right now. The person's click is the approval."""
    if db.query(ClassReminder).filter_by(class_id=approval.class_id, stage=approval.stage).first():
        raise HTTPException(status_code=409, detail="This reminder has already been approved")
    match = next((r for r in _due(db, today)
                  if r["class"].id == approval.class_id and r["stage"] == approval.stage), None)
    if not match:
        raise HTTPException(status_code=404, detail="This reminder is not due")

    now = datetime.utcnow()
    campaign = EmailCampaign(
        title=f"Reminder: {match['class'].name} ({match['label']})",
        subject=approval.subject,
        body=approval.body,
        recipient_tags="",
        recipient_lists=EMAIL_LIST,
        recipient_count=len(match["recipients"]),
        status="sent",
        sent_at=now,
    )
    db.add(campaign)
    db.flush()
    db.add_all(EmailRecipient(campaign_id=campaign.id, student_id=s.id, email_address=s.email, status="pending")
               for s in match["recipients"])
    db.add(ClassReminder(class_id=approval.class_id, stage=approval.stage, campaign_id=campaign.id, approved_at=now))
    try:
        db.commit()
    except IntegrityError:  # approved twice at the same moment
        db.rollback()
        raise HTTPException(status_code=409, detail="This reminder has already been approved")
    return {"campaign_id": campaign.id, "recipients_count": len(match["recipients"]),
            "message": f"Reminder recorded for {len(match['recipients'])} students"}
