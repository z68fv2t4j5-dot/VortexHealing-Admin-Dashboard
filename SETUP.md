# VortexHealing Admin Dashboard - Setup Guide

## Prerequisites

- **Python 3.9+**
- **Node.js 16+** & **npm**
- **PostgreSQL 13+** (or use Docker)
- **LM Studio** with Qwen model loaded (for AI features)
- **Docker & Docker Compose** (optional, for containerized setup)

---

## Quick Start (Development)

### 1. Backend Setup

```bash
cd backend

# Copy environment file
cp .env.example .env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (first time)
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start backend
python main.py
```

Backend runs on: **http://localhost:8001**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend runs on: **http://localhost:3000**

---

## Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8001
# - PostgreSQL: localhost:5432
```

---

## Environment Configuration

### Backend (.env file)

```env
DATABASE_URL=postgresql://vortex:vortex@localhost:5432/vortexhealing
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LM_STUDIO_URL=http://localhost:1234/v1
QWEN_MODEL=qwen3.8-27b
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@vortexhealing.com
FRONTEND_URL=http://localhost:3000
```

---

## API Documentation

Once backend is running:

- **Interactive API Docs (Swagger UI)**: http://localhost:8001/docs
- **Alternative Docs (ReDoc)**: http://localhost:8001/redoc

---

## Database Setup (PostgreSQL)

### Option 1: Local PostgreSQL

```bash
# Create database
createdb vortexhealing

# Create user (if not exists)
psql -c "CREATE USER vortex WITH PASSWORD 'vortex';"
psql -c "ALTER USER vortex CREATEDB;"
```

### Option 2: Docker PostgreSQL

```bash
docker run --name vortex-postgres \
  -e POSTGRES_USER=vortex \
  -e POSTGRES_PASSWORD=vortex \
  -e POSTGRES_DB=vortexhealing \
  -p 5432:5432 \
  -d postgres:15-alpine
```

---

## AI Features (Qwen Integration)

### Setup LM Studio

1. Download **LM Studio** from https://lmstudio.ai
2. Open LM Studio
3. Go to **Discover** tab
4. Search for **qwen3.8-27b**
5. Click **Download**
6. Once downloaded, click **Load Model**
7. Wait for server to start (shows "Server is running")

### Using AI Features

The dashboard uses Qwen for:
- **Growth Ideas Generation**: AI-generated business suggestions
- **Document Summarization**: Auto-summarize uploaded documents
- **Task Analysis**: Help with task descriptions

---

## Features Overview

### Dashboard
- Quick stats overview
- Recent tasks
- Quick action buttons
- System health status

### Students Management
- Add/edit/delete students
- Track enrollment
- View contact information
- Enrollment history

### Classes
- Schedule management
- Capacity tracking
- Prerequisites setup
- Class descriptions

### Events
- Event scheduling
- Event type categorization
- Location management
- Attendee tracking

### Tasks
- Daily/weekly/one-time tasks
- Priority levels
- Status tracking (todo, in_progress, done)
- Due date management

### Email Campaigns
- Email template management
- Campaign scheduling
- Recipient list management
- Send/schedule emails

### Growth Ideas
- AI-generated suggestions using Qwen
- Category organization
- Impact assessment
- Implementation difficulty rating

### Accounting Documents
- Document upload (PDF, DOCX, TXT)
- Document storage
- Organization
- Quick access

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8001 is in use
lsof -i :8001

# Kill process if needed
kill -9 <PID>
```

### Database connection error
```bash
# Test PostgreSQL connection
psql -U vortex -d vortexhealing -c "SELECT 1"

# Check DATABASE_URL in .env
```

### Frontend can't reach backend
- Ensure backend is running on port 8001
- Check if CORS is enabled in backend
- Verify API_URL in frontend environment

### Qwen AI not working
- Ensure LM Studio is running
- Verify model is loaded
- Check LM_STUDIO_URL in .env (should be http://localhost:1234/v1)
- Test: `curl http://localhost:1234/v1/models`

### Port already in use
```bash
# Change port in vite.config.ts (frontend) or main.py (backend)
# Or kill existing process
```

---

## Production Deployment

### Before deploying:

1. Change `SECRET_KEY` to a secure random string
2. Set `ALGORITHM` to appropriate value
3. Update `DATABASE_URL` to production database
4. Set `FRONTEND_URL` to production domain
5. Configure email credentials for MAIL_* variables
6. Use environment-specific settings

### Deploy with Docker:

```bash
# Build images
docker-compose build

# Push to registry
docker push your-registry/vortex-api:latest
docker push your-registry/vortex-ui:latest

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

---

## Development Commands

### Backend

```bash
# Run tests
pytest

# Format code
black .

# Lint
flake8 .

# Create database migration
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

---

## Project Structure

```
VortexHealing-Admin-Dashboard/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core config & database
│   │   ├── models.py     # Database models
│   │   └── schemas.py    # Pydantic schemas
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── styles/       # CSS files
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Support & Contributing

For issues and feature requests, please refer to the project documentation.

---

## License

MIT License - See LICENSE file for details
