import os

# Must be set before app.core.config is imported: the default URL is Postgres,
# and tests must never touch the real vortexhealing.db.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.api import email_campaigns
from app.models import Student


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Student(first_name="Ana", last_name="One", email="ana@example.com",
                tags="SRA, Active, Sensing I, 26-01-S1, MS-Cert", lists="APAC Wizards, Free Events"),
        Student(first_name="Ben", last_name="Two", email="ben@example.com",
                tags="Active, Omega", lists="Global Wizards"),
        Student(first_name="Cal", last_name="Three", email="cal@example.com",
                tags="Foundational", lists="APAC Wizards"),
        Student(first_name="Dee", last_name="NoEmail", email=None,
                tags="Active", lists="APAC Wizards"),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture
def client(db):
    # Only the email router: main.py also loads the handouts index and its ML model
    app = FastAPI()
    app.include_router(email_campaigns.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)
