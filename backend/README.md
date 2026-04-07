# AI-Native PMS Backend (FastAPI)

Production-grade backend module for a Performance Management System with role-based login, JWT auth, role-based authorization, async PostgreSQL access, and Alembic migrations.

## Stack
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy 2.0 Async ORM
- Alembic migrations
- JWT authentication (`user_id`, `organization_id`, `role` claims)
- RBAC (Employee, Manager, HR, Leadership, Admin)
- SlowAPI rate limiting
- Docker-ready

## Project Structure

```text
backend/
  app/
    ai/
    main.py
    config.py
    database.py
    models/
    schemas/
    services/
    routers/
    auth/
    core/
    utils/
  migrations/
  Dockerfile
  requirements.txt
```

## Authentication Flow
1. Frontend sends role login payload (`role`, `email`, `name`) to `POST /api/v1/auth/role-login`
2. Backend finds or creates user and organization (by domain)
3. Assigns role
4. Issues JWT access token

## RBAC Rules
- Employee: own goals, progress updates, check-in requests
- Manager: approve team goals, submit ratings, generate reviews
- HR: org-level visibility + analytics
- Leadership: read-only analytics/insights
- Admin: full organizational/role control

## Environment
Copy `.env.example` to `.env` and update values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

PostgreSQL connection examples:
- Local backend on host machine: `postgresql+asyncpg://postgres:shiv@localhost:5432/pms`
- Backend running in Docker compose: `postgresql+asyncpg://postgres:shiv@db:5432/pms`

## Local Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Seed Mock Data
Use the seed script to populate realistic demo records for dashboards and key workflows:

```bash
python -m alembic -c migrations/alembic.ini upgrade head
PYTHONPATH=. python scripts/seed_mock_data.py
```

This seeds organizations, users, performance cycles, goals, check-ins, ratings, and reviews.

## Alembic Migration
```bash
alembic -c migrations/alembic.ini upgrade head
```

## Docker
```bash
docker build -t pms-backend .
docker run --env-file .env -p 8000:8000 pms-backend
```

## Implemented API Endpoints

### Auth
- `POST /api/v1/auth/role-login`
- `GET /api/v1/auth/me`

### Users
- `GET /api/v1/users/me`
- `GET /api/v1/users/team`
- `PATCH /api/v1/users/update`

### Employees
- `GET /api/v1/employees`
- `GET /api/v1/employees/{id}`
- `GET /api/v1/employees/manager/{manager_id}`
- `POST /api/v1/employees` (Admin only)
- `PATCH /api/v1/employees/{id}` (Admin only)
- `DELETE /api/v1/employees/{id}` (Admin only)

### Performance Cycles
- `GET /api/v1/performance-cycles`
- `GET /api/v1/performance-cycles/active`
- `GET /api/v1/performance-cycles/framework/recommend?role=...&department=...`
- `POST /api/v1/performance-cycles` (HR/Admin only)
- `PATCH /api/v1/performance-cycles/{id}` (HR/Admin only)

### Organizations
- `POST /api/v1/organizations`
- `POST /api/v1/organizations/{org_id}/assign-user`

### Goals
- `POST /api/v1/goals`
- `GET /api/v1/goals`
- `PATCH /api/v1/goals/{goal_id}`
- `POST /api/v1/goals/{goal_id}/submit`
- `POST /api/v1/goals/{goal_id}/approve`

### Check-ins
- `POST /api/v1/checkins`
- `GET /api/v1/checkins`
- `PATCH /api/v1/checkins/{checkin_id}/complete`

### Ratings
- `POST /api/v1/ratings`
- `GET /api/v1/ratings`
- `GET /api/v1/ratings/weighted-score/{employee_id}`

### Reviews
- `GET /api/v1/reviews`
- `POST /api/v1/reviews/generate`
- `GET /api/v1/reviews/analytics`

### AI
- `POST /api/v1/ai/goals/suggest`
- `POST /api/v1/ai/checkins/summarize`
- `POST /api/v1/ai/review/generate`
- `POST /api/v1/ai/feedback/coach`
- `POST /api/v1/ai/growth/suggest`
- `POST /api/v1/ai/training/suggest`
- `POST /api/v1/ai/decision/insights`

### Meetings and Calendar
- `GET /api/v1/calendar/availability`
- `POST /api/v1/meetings/create`
- `GET /api/v1/meetings`
- `GET /api/v1/meetings/{meeting_id}`
- `PATCH /api/v1/meetings/{meeting_id}`
- `DELETE /api/v1/meetings/{meeting_id}`
- `POST /api/v1/meetings/{meeting_id}/transcript-sync`
- `GET /api/v1/meetings/analytics/summary`

Calendar and Meet endpoints use server-side Google OAuth token refresh. Frontend does not send Google access tokens.

Required Google OAuth scopes:
- `openid`
- `email`
- `profile`
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`

Google authorization is requested with `access_type=offline` and `prompt=consent` so a refresh token can be stored for each user.

## AI Access and Usage Limits
- Employee: goal suggestions, career growth suggestions (3 uses per quarter)
- Manager: feedback coaching, review summaries, decision insights (10 uses per quarter)
- HR: training suggestions, decision insights (20 uses per quarter)
- Leadership: decision insights
- Admin: full AI access

Usage is tracked in `ai_usage_logs` with `prompt_tokens`, `response_tokens`, and timestamp.

## Example AI Responses

`POST /api/v1/ai/checkins/summarize`
```json
{
  "summary": "The employee completed milestone 1 and highlighted a blocker in QA handoff.",
  "key_points": ["Milestone achieved", "QA dependency risk", "Need weekly sync"],
  "action_items": ["Manager to align QA owner", "Employee to share revised timeline"]
}
```

`POST /api/v1/ai/feedback/coach`
```json
{
  "improved_feedback": "Your execution has improved; focus next on earlier risk communication.",
  "tone_score": 8,
  "suggested_version": "Great progress this cycle. In the next sprint, please raise blockers by day 2 so we can support faster."
}
```
