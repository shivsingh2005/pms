# PMS

AI-native Performance Management System (PMS) with role-based workflows for goals, check-ins, ratings, reviews, and meeting orchestration.

## Tech Stack
- Backend: FastAPI, SQLAlchemy (async), Alembic, PostgreSQL
- Frontend: Next.js 14, TypeScript, Tailwind CSS, Zustand
- AI and Integrations: Gemini APIs, Google Calendar/Meet
- Infrastructure: Docker Compose, Vercel (frontend), Cloud Run (backend)

## Features
- Role-based login and JWT authentication
- RBAC for Employee, Manager, HR, Leadership, and Admin
- Goal lifecycle management (draft, submit, approve)
- Scheduled check-ins with AI summarization
- Ratings and performance review workflows
- Google Calendar and Meet scheduling support
- AI-assisted coaching and decision insights

## Repository Layout
- `backend/` - API service, domain models, migrations, tests
- `frontend/` - Web app, UI components, stores, service clients
- `DEPLOYMENT.md` - Production deployment guidance
- `document.md` - Project technical documentation

## Local Setup
### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional but recommended)

### 1) Backend
```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m alembic -c migrations/alembic.ini upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2) Frontend
```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`
Backend: `http://127.0.0.1:8000`

## Environment Variables
### Backend (`backend/.env`)
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `CORS_ALLOW_ORIGINS`

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL`

## Run Tests
```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

## Build Frontend
```powershell
cd frontend
npm run build
```

## Deployment
Use `DEPLOYMENT.md` for Cloud Run + Vercel deployment steps.

## Security
- Never commit secrets or `.env` files
- Restrict CORS to trusted origins
- Rotate API/JWT keys periodically
