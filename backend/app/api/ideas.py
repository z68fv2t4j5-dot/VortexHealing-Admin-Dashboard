from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import GrowthIdea
from app.schemas import IdeaCreate, IdeaResponse
from typing import List
from openai import OpenAI
from app.core.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.SECRET_KEY, base_url=settings.LM_STUDIO_URL)

@router.post("/", response_model=IdeaResponse)
async def create_idea(idea: IdeaCreate, db: Session = Depends(get_db)):
    db_idea = GrowthIdea(**idea.dict())
    db.add(db_idea)
    db.commit()
    db.refresh(db_idea)
    return db_idea

@router.get("/", response_model=List[IdeaResponse])
async def get_ideas(db: Session = Depends(get_db)):
    return db.query(GrowthIdea).all()

@router.post("/generate")
async def generate_ideas(category: str = "student_growth", db: Session = Depends(get_db)):
    try:
        response = client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=[
                {"role": "system", "content": "You are an educational institution growth strategy expert."},
                {"role": "user", "content": f"Generate 5 innovative ideas for {category} for an educational institution."}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        ideas_text = response.choices[0].message.content
        idea = GrowthIdea(
            title=f"AI Generated Ideas - {category}",
            description=ideas_text,
            category=category,
            potential_impact="High",
            implementation_difficulty="Medium",
            status="pending"
        )
        db.add(idea)
        db.commit()
        db.refresh(idea)
        return idea
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{idea_id}")
async def delete_idea(idea_id: int, db: Session = Depends(get_db)):
    idea = db.query(GrowthIdea).filter(GrowthIdea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    db.delete(idea)
    db.commit()
    return {"deleted": True}
