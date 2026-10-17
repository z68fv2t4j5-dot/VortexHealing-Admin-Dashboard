from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None

class StudentResponse(StudentCreate):
    id: int
    enrollment_date: datetime
    status: str
    class Config:
        from_attributes = True

class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instructor: str
    capacity: int
    schedule: str
    prerequisites: Optional[str] = None
    start_date: datetime
    end_date: datetime

class ClassResponse(ClassCreate):
    id: int
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: str
    event_type: str

class EventResponse(EventCreate):
    id: int
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 0
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None

class TaskResponse(TaskCreate):
    id: int
    status: str
    completed_at: Optional[datetime]
    class Config:
        from_attributes = True

class EmailCampaignCreate(BaseModel):
    name: str
    subject: str
    body: str
    recipients: str
    scheduled_time: datetime

class EmailCampaignResponse(EmailCampaignCreate):
    id: int
    sent: bool
    class Config:
        from_attributes = True

class IdeaCreate(BaseModel):
    title: str
    description: str
    category: str
    potential_impact: str
    implementation_difficulty: str

class IdeaResponse(IdeaCreate):
    id: int
    status: str
    class Config:
        from_attributes = True

class DocumentCreate(BaseModel):
    filename: str
    doc_type: str
    content: str

class DocumentResponse(DocumentCreate):
    id: int
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
