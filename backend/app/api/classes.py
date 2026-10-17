from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Class
from app.schemas import ClassCreate, ClassResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=ClassResponse)
async def create_class(cls: ClassCreate, db: Session = Depends(get_db)):
    db_class = Class(**cls.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.get("/", response_model=List[ClassResponse])
async def get_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()

@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls

@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(class_id: int, class_update: ClassCreate, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    for field, value in class_update.dict().items():
        setattr(cls, field, value)
    db.commit()
    db.refresh(cls)
    return cls

@router.delete("/{class_id}")
async def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()
    return {"deleted": True}
