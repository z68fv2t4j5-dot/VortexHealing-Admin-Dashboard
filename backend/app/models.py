from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.ADMIN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    lists = Column(String)  # Comma-separated lists (e.g., "APAC Wizards, Interested in VortexHealing")
    tags = Column(String)   # Comma-separated tags (e.g., "SRA, Active")
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text)
    instructor = Column(String)
    capacity = Column(Integer)
    schedule = Column(String)
    prerequisites = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String)
    event_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Integer, default=0)
    assigned_to = Column(String)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    recipient_tags = Column(String)  # Comma-separated tags to filter
    recipient_lists = Column(String) # Comma-separated lists to filter
    recipient_count = Column(Integer, default=0)
    status = Column(String, default="draft")  # draft, sent, failed, scheduled
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailRecipient(Base):
    __tablename__ = "email_recipients"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("email_campaigns.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    email_address = Column(String)
    sent_at = Column(DateTime)
    status = Column(String, default="pending")  # pending, sent, failed
    error_message = Column(String)

class GrowthIdea(Base):
    __tablename__ = "growth_ideas"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    potential_impact = Column(String)
    implementation_difficulty = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    file_path = Column(String)
    doc_type = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class GlobalStudent(Base):
    __tablename__ = "global_students"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    address_1 = Column(String)
    address_2 = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country = Column(String)
    notes = Column(Text)
    # All other columns stored as JSON for class enrollments/courses
    all_data = Column(Text)  # JSON string with all columns
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
