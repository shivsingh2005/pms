# PMS Technical Documentation

## 1. Overview
This repository contains an AI-native Performance Management System (PMS) built with:
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL, Alembic
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand
- Integrations: Google Calendar / Google Meet, Gemini-based AI workflows

The platform supports goal setting, check-ins, ratings, reviews, and AI-assisted insights across multiple organizational roles.

## 2. Repository Structure
- `backend/`: FastAPI service, business logic, DB models, migrations, tests
- `frontend/`: Next.js web application, UI components, state stores, API clients
- `docker-compose.yml`: Local multi-service stack definition
- `DEPLOYMENT.md`: Cloud deployment guidance

## 3. Functional Modules
- Authentication and authorization: role-based login with JWT
- Goals: create, update, submit, approve
- Check-ins: schedule and complete manager-employee check-ins
- Meetings: Google Calendar event scheduling with Meet links
- Ratings and reviews: performance scoring and review generation
- AI features: coaching, summaries, growth suggestions, decision support

## 4. Environment Configuration
### Backend (`backend/.env`)
Key variables include:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `CORS_ALLOW_ORIGINS`

### Frontend (`frontend/.env.local`)
Key variable:
- `NEXT_PUBLIC_API_BASE_URL`

## 5. Local Runbook
### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional for cache/rate-limit features)

### Backend
1. `cd backend`
2. `..\.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. `..\.venv\Scripts\python.exe -m alembic -c migrations/alembic.ini upgrade head`
4. `..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## 6. API and Security Notes
- API base path: `/api/v1`
- Health endpoint: `/health`
- JWT claims include `user_id`, `organization_id`, and `role`
- CORS origins must include frontend host(s), e.g. `http://localhost:3000`

## 7. Testing
### Backend tests
- `cd backend`
- `..\.venv\Scripts\python.exe -m pytest -q`

### Frontend verification
- `cd frontend`
- `npm run build`

## 8. Deployment Summary
- Backend: Cloud Run (or container platform)
- Frontend: Vercel
- Database: Managed PostgreSQL
- Cache: Managed Redis
Refer to `DEPLOYMENT.md` for full deployment steps.

## 9. Operational Best Practices
- Do not commit `.env` files or secrets
- Rotate JWT and API credentials regularly
- Run migrations in CI/CD before app rollout
- Monitor API errors, DB performance, and rate-limit metrics
