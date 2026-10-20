# VortexHealing Admin Dashboard - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    VortexHealing Admin Dashboard            │
├─────────────────────────────────────────────────────────────┤
│ Frontend (React 18 + TypeScript + Vite)                    │
│ ├── Pages: Dashboard, Students, GlobalStudents, Classes    │
│ ├── Pages: Tasks, Handouts, Chat, Email, Ideas            │
│ └── State: React Query + Local hooks                       │
├─────────────────────────────────────────────────────────────┤
│ Backend (FastAPI + SQLAlchemy + SQLite)                    │
│ ├── API Routes: /api/students, /api/classes, /api/tasks   │
│ ├── API Routes: /api/handouts, /api/ai, /api/chat         │
│ ├── Database: SQLite (local, no server needed)             │
│ └── LLM Integration: Qwen 3.8 via localhost:1234/v1       │
├─────────────────────────────────────────────────────────────┤
│ Data Sources                                                │
│ ├── Students: CSV import from All Contacts folder          │
│ ├── Classes: Hardcoded seed (27 classes)                   │
│ ├── Handouts: 100 PDFs/DOCs with semantic embeddings       │
│ └── Tasks: AI-generated via Qwen                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Frontend
- **Handouts.tsx**: Semantic search + AI Q&A for 100 documents
- **GlobalStudents.tsx**: Searchable database of 7000+ contacts
- **Classes.tsx**: 27 classes with schedule information
- **Tasks.tsx**: Task management with AI generation
- **Navigation.tsx**: Unified left sidebar with all pages

### Backend
- **main.py**: FastAPI app entry point
- **models.py**: SQLAlchemy ORM models
- **handouts_service.py**: Semantic search with embeddings
- **app/api/**: Route modules for each feature
- **seed_*.py**: Data import scripts

### Data Flow
```
CSV (All Contacts)      PDF/DOC (Handouts)      Schedule
    ↓                           ↓                  ↓
seed_students.py        handouts_service.py   seed_classes.py
    ↓                           ↓                  ↓
SQLite DB ←─────────────────────────────────────→ Index (JSON)
    ↓                                              ↓
FastAPI routes ←───────────────────────────────→ Search
    ↓                                              ↓
React UI ←────────────────────────────────────────→ Display
```

## Technology Choices

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | React 18 | Modern, component-based |
| Backend | FastAPI | Fast, async, auto-docs |
| Database | SQLite | Local, no server needed |
| LLM | Qwen 3.8 | Local, private, runs on LM Studio |
| Search | sentence-transformers | Small, fast embeddings |
| State | React Query | Caching, mutations, refetch |

## Handouts Knowledge Base Architecture

```
100 Handout Documents (PDF/DOC)
    ↓
Extract Text (pypdf, python-docx)
    ↓
Chunk Text (sentences ~500 chars each)
    ↓
Generate Embeddings (all-MiniLM-L6-v2)
    ↓
Store Index (handouts_index.json - 154MB)
    ↓
FastAPI Routes:
  - GET /api/handouts/search → Semantic + keyword matching
  - POST /api/handouts/ask → Search + Qwen AI response
  - GET /api/handouts/list → Show indexed documents count
```

## Semantic Search Implementation

1. **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
2. **Search Algorithm**: 
   - Encode query with model
   - Calculate cosine similarity with all chunk embeddings
   - Combine semantic score (0-100) with keyword bonus
   - Return top N results sorted by score
3. **Scoring**: 
   - Base: Semantic similarity (cosine)
   - Bonus: +20 for filename match, +10 for full-text keyword match

## Current Limitations & Next Work

| Issue | Status | Fix |
|-------|--------|-----|
| Index file (154MB) | 🔄 In .gitignore | Not tracked in git |
| Preview text only | 🔴 Open | Return full chunk text to Qwen |
| Model auto-download | 🟡 Works | Pre-download optional |
| Index at startup | ✅ Done | Eager initialization |
| Missing chunk text for Qwen | 🔴 Open | Modify ask endpoint to return chunk |

