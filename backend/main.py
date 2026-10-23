from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import threading

from app.core.config import settings
from app.core.database import Base, engine
from handouts import ingest as handouts_ingest
from app.api import tasks, students, classes, events, emails, ideas, auth, documents, global_students, admin, ai_tasks, handouts, email_campaigns, reminders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting VortexHealing Admin Dashboard")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")
    if settings.HANDOUTS_DIR:
        # Picks up new or revised handouts; unchanged files are skipped, so this is quick.
        threading.Thread(target=handouts_ingest.run_quietly, daemon=True).start()
    yield
    logger.info("🛑 Shutting down")

app = FastAPI(
    title="VortexHealing Admin Dashboard API",
    description="Complete admin platform for educational institutions",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "VortexHealing Admin Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(ai_tasks.router, prefix="/api", tags=["ai_tasks"])
app.include_router(handouts.router, prefix="/api", tags=["handouts"])
app.include_router(email_campaigns.router, prefix="/api", tags=["email_campaigns"])
app.include_router(reminders.router, prefix="/api", tags=["reminders"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(global_students.router, prefix="/api", tags=["global_students"])
app.include_router(classes.router, prefix="/api/classes", tags=["classes"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(ideas.router, prefix="/api/ideas", tags=["ideas"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
