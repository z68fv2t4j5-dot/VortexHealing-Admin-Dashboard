# AGENTS.md - VortexHealing Admin Dashboard Governance

## Agent Collaboration Standards

This document establishes how Claude Code, Cursor, and other AI agents collaborate on the VortexHealing Admin Dashboard project.

### Core Principles

1. **Local-First Development**: No cloud dependencies (Qwen runs locally via LM Studio)
2. **Data Privacy**: Student data never leaves the local environment
3. **Incremental Commits**: Each feature gets its own commit with clear messages
4. **Memory Over Chat**: Decisions are documented in `docs/memory/` for continuity
5. **Test-Driven**: Changes are verified in the browser before committing

### Project Rules

#### Frontend (React/TypeScript)
- ✅ Use React Query for data fetching
- ✅ Use Tailwind-inspired CSS for styling
- ✅ All pages go in `src/pages/`
- ✅ All components go in `src/components/`
- ❌ No external UI libraries (build with raw HTML/CSS)
- ✅ Responsive design for mobile

#### Backend (FastAPI/Python)
- ✅ Use SQLAlchemy ORM for database
- ✅ SQLite for local development
- ✅ JWT for authentication
- ✅ Clear API route organization (`app/api/`)
- ✅ Seed scripts for data import
- ✅ CORS enabled for frontend communication

#### Data Management
- ✅ Weekly updates from `/Users/djw/Documents/VortexHealing Assistant Docs/All Contacts/`
- ✅ Re-run `seed_students.py` after CSV updates
- ✅ Class data maintained in `seed_classes.py`
- ✅ Database schema in `app/models.py`

#### Git Workflow
- Feature branches before major changes
- Meaningful commit messages (what + why)
- Attribution line: `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`
- One feature per commit (atomic)

### Agent Responsibilities

#### Code Changes
- **Read First**: Always read relevant files before editing
- **Plan Mode**: Use EnterPlanMode for non-trivial changes (3+ files or architectural decisions)
- **Test Immediately**: Restart servers and test in browser before committing
- **Document Decisions**: Update `docs/memory/` with why, not just what

#### Data/Database
- **Backups**: Always back up SQLite before major migrations
- **Schema Changes**: Update models.py, then re-run seed scripts
- **Data Validation**: Verify counts after seeding (1771 students, 27 classes)

#### Integration Points
- Frontend talks to Backend API at `http://localhost:8000/api`
- LM Studio Qwen available at `http://localhost:1234/v1`
- Chat requires LM Studio running; gracefully handle disconnection

### Decision Log

Decisions made during development are recorded in `docs/memory/` with:
- **What**: The decision or change
- **Why**: The reasoning (constraints, user request, technical limitation)
- **When**: Date made
- **Impact**: What else it affects

### Communication

When agents work together:
1. **Read memory first** to understand prior decisions
2. **Document new decisions** before implementation
3. **Test independently** before committing
4. **Ask before major changes** (via EnterPlanMode for architectural decisions)

### No-Gos

❌ Delete student or class data without backup
❌ Push to main without testing locally
❌ Commit without clear message
❌ Modify database schema without updating models.py
❌ Ignore CORS or security implications

### Success Criteria

✅ Dashboard displays students (1771+) searchable by name/email
✅ Classes display with calendar view (27 classes)
✅ Chat works when LM Studio is running
✅ Email campaigns can segment by Tags/Lists
✅ No error messages in browser console
✅ All seed operations complete successfully

---

*This governance structure enables async collaboration where multiple AI agents can work on this project independently while maintaining coherence and avoiding conflicts.*
