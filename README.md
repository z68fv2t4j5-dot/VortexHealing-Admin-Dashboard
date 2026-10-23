# VortexHealing Admin Dashboard

Complete full-stack admin platform for educational institutions with task management, student/customer database, class scheduling, event management, and AI-powered growth insights.

## Features

### Dashboard
- Daily/Weekly task management and calendar
- Event notifications and scheduling
- Quick stats and overview

### Student/Customer Management
- Student profiles and enrollment tracking
- Customer database with contact info
- Progress tracking and history

### Class Management
- Schedule management with prerequisites
- Class capacity and attendance
- Prerequisites and course requirements

### Admin Automation
- Automated task workflows
- Email campaign scheduling
- Task automation rules

### Marketing
- Email template management
- Campaign scheduling and automation
- Marketing automation workflows

### Accounting
- Documentation management
- Financial records
- Expense tracking

### Growth Ideas
- AI-generated growth suggestions using local Qwen
- Strategy recommendations
- Performance analytics

### Voice Interface
- Voice command support
- Audio input processing
- Voice-based task management

## Tech Stack

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- React Query
- Axios

**Backend:**
- Python FastAPI
- SQLAlchemy ORM
- PostgreSQL
- JWT Authentication
- Qwen AI Integration (local)

**Mobile:**
- React Native + Expo
- Shared API with backend

**Voice:**
- Speech-to-text API
- Voice command processing

**Deployment:**
- Docker & Docker Compose
- PostgreSQL container
- FastAPI server

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL (or use Docker)
- LM Studio with Qwen loaded

### Backend Setup

```bash
cd backend
cp .env.example .env
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8001`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

### Using Docker

```bash
docker-compose up
```

## API Documentation

- **Interactive Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Project Structure

```
VortexHealing-Admin-Dashboard/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── core/           # Config, security, db
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── mobile/                  # React Native app
├── docker-compose.yml
├── README.md
└── SETUP.md
```

## Documentation

- [Setup Guide](SETUP.md) - Detailed installation
- [API Documentation](docs/api.md) - API endpoints
- [Architecture](docs/architecture.md) - System design

## License

MIT
