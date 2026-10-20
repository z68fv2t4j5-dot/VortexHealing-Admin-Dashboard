from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import GlobalStudent
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Dict, Any
import json

router = APIRouter()

class GlobalStudentSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    all_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('all_data', mode='before')
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}

@router.get("/global-students", response_model=list[GlobalStudentSchema])
async def get_global_students(db: Session = Depends(get_db)):
    students = db.query(GlobalStudent).all()
    return students

@router.get("/global-students/search")
async def search_global_students(q: str, db: Session = Depends(get_db)):
    search_term = f"%{q.lower()}%"
    results = db.query(GlobalStudent).filter(
        (GlobalStudent.first_name.ilike(search_term)) |
        (GlobalStudent.last_name.ilike(search_term)) |
        (GlobalStudent.email.ilike(search_term)) |
        (GlobalStudent.city.ilike(search_term)) |
        (GlobalStudent.country.ilike(search_term)) |
        (GlobalStudent.all_data.ilike(search_term))
    ).all()
    return results

@router.get("/global-students/{student_id}", response_model=GlobalStudentSchema)
async def get_global_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(GlobalStudent).filter(GlobalStudent.id == student_id).first()
    return student


