from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import EmailCampaign, EmailRecipient, Student
from pydantic import BaseModel
from datetime import datetime
import httpx

router = APIRouter()

class EmailCampaignCreate(BaseModel):
    title: str
    subject: str
    body: str
    recipient_tags: str = ""
    recipient_lists: str = ""

class EmailCampaignResponse(BaseModel):
    id: int
    title: str
    subject: str
    body: str
    recipient_tags: str
    recipient_lists: str
    recipient_count: int
    status: str
    created_at: datetime

def filter_students_by_tags_and_lists(db: Session, tags: str, lists: str):
    """Filter students by comma-separated tags and lists"""
    students = db.query(Student).filter(Student.email.isnot(None)).all()

    if not tags and not lists:
        return students

    tag_list = [t.strip().lower() for t in tags.split(',') if t.strip()]
    list_list = [l.strip().lower() for l in lists.split(',') if l.strip()]

    filtered = []
    for student in students:
        # Check tags match
        if tag_list:
            student_tags = [t.strip().lower() for t in (student.tags or "").split(',')]
            if not any(tag in student_tags for tag in tag_list):
                continue

        # Check lists match
        if list_list:
            student_lists = [l.strip().lower() for l in (student.lists or "").split(',')]
            if not any(lst in student_lists for lst in list_list):
                continue

        filtered.append(student)

    return filtered

@router.post("/email/campaigns", response_model=EmailCampaignResponse)
async def create_campaign(campaign: EmailCampaignCreate, db: Session = Depends(get_db)):
    """Create a new email campaign"""
    students = filter_students_by_tags_and_lists(db, campaign.recipient_tags, campaign.recipient_lists)

    db_campaign = EmailCampaign(
        title=campaign.title,
        subject=campaign.subject,
        body=campaign.body,
        recipient_tags=campaign.recipient_tags,
        recipient_lists=campaign.recipient_lists,
        recipient_count=len(students),
        status="draft"
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/email/campaigns", response_model=list[EmailCampaignResponse])
async def list_campaigns(db: Session = Depends(get_db)):
    """List all email campaigns"""
    campaigns = db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).all()
    return campaigns

@router.post("/email/preview")
async def preview_campaign(campaign: EmailCampaignCreate, db: Session = Depends(get_db)):
    """Preview campaign to sample recipients"""
    students = filter_students_by_tags_and_lists(db, campaign.recipient_tags, campaign.recipient_lists)
    sample = students[:5] if students else []

    return {
        "total_recipients": len(students),
        "sample_count": len(sample),
        "sample_recipients": [
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "email": s.email
            }
            for s in sample
        ]
    }

@router.post("/email/send")
async def send_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Send campaign to recipients"""
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not campaign:
        return {"error": "Campaign not found"}

    students = filter_students_by_tags_and_lists(db, campaign.recipient_tags, campaign.recipient_lists)

    # Create EmailRecipient records for tracking
    for student in students:
        recipient = EmailRecipient(
            campaign_id=campaign.id,
            student_id=student.id,
            email_address=student.email,
            status="pending"
        )
        db.add(recipient)

    campaign.status = "sent"
    campaign.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)

    return {
        "status": "success",
        "campaign_id": campaign.id,
        "recipients_count": len(students),
        "message": f"Campaign sent to {len(students)} recipients"
    }

@router.get("/students/filter")
async def filter_students(tags: str = "", lists: str = "", db: Session = Depends(get_db)):
    """Filter students by tags and lists"""
    students = filter_students_by_tags_and_lists(db, tags, lists)
    return {
        "count": len(students),
        "students": [
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "email": s.email,
                "tags": s.tags,
                "lists": s.lists
            }
            for s in students
        ]
    }
