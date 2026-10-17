from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import EmailCampaign
from app.schemas import EmailCampaignCreate, EmailCampaignResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=EmailCampaignResponse)
async def create_campaign(campaign: EmailCampaignCreate, db: Session = Depends(get_db)):
    db_campaign = EmailCampaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/", response_model=List[EmailCampaignResponse])
async def get_campaigns(db: Session = Depends(get_db)):
    return db.query(EmailCampaign).order_by(EmailCampaign.scheduled_time).all()

@router.get("/{campaign_id}", response_model=EmailCampaignResponse)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.post("/{campaign_id}/send")
async def send_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    from datetime import datetime
    campaign.sent = True
    campaign.sent_at = datetime.utcnow()
    db.commit()
    return {"sent": True}

@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(campaign)
    db.commit()
    return {"deleted": True}
