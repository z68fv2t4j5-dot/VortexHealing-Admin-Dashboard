# VortexHealing Admin Dashboard - Agentic Development Harness

## Project Overview

The VortexHealing Admin Dashboard is a full-stack application built with AI-agent collaboration, combining:
- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Data Sources**: Student contacts (CSV), Class schedules (PDF)
- **AI Features**: Local Qwen 3.8 via LM Studio for chat, idea generation, and document processing

## Bootstrap Environment

This project uses the MKC Agentic Development Harness to enable structured collaboration between human developers and AI agents (Claude Code, Cursor, etc.).

### Key Features

✅ **Structured Memory**: Session transcripts in `docs/memory/` for context tracking
✅ **Governance Docs**: `AGENTS.md` defines collaboration rules
✅ **Enforcement**: Git hooks validate commits before pushing
✅ **Skills**: Reusable scripts and seed functions (`seed_students.py`, `seed_classes.py`)
✅ **Multi-Stage Pipeline**: Backend API → Frontend UI → Database

## Quick Start

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python main.py  # Runs on localhost:8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Runs on localhost:3000

# Seed Data
python seed_students.py  # Imports from All Contacts CSV
python seed_classes.py   # Imports from VortexHealing schedule
```

## Development Workflow

1. **Plan**: Document approach in `docs/memory/`
2. **Code**: Changes to backend or frontend
3. **Commit**: Use meaningful messages with context
4. **Test**: Verify in browser at localhost:3000
5. **Document**: Update memory with decisions and learnings

## Data Flow

```
All Contacts CSV (1771 students)
         ↓
    seed_students.py
         ↓
    SQLite Database
         ↓
    FastAPI (/api/students)
         ↓
    React Frontend
         ↓
    Searchable/Filterable UI
```

## Next Phases

- [ ] Email campaign system (using Tags/Lists for segmentation)
- [ ] Email scheduling via Qwen AI
- [ ] Analytics & reporting dashboard
- [ ] Voice interface via speech-to-text
- [ ] Mobile React Native app
- [ ] Weekly data sync automation

## Configuration

- **Database**: SQLite (local, no server needed)
- **LLM**: Qwen 3.8 via LM Studio on localhost:1234/v1
- **Environment**: Python 3.12, Node.js 18+, React 18

See `AGENTS.md` for governance rules and collaboration standards.
