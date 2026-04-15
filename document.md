# PMS Technical Documentation

## 1. Overview
This repository contains an AI-native Performance Management System (PMS) built with:
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL, Alembic
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand
- Integrations: Google Calendar / Google Meet, Gemini-based AI workflows

The platform supports goal setting, check-ins, ratings, reviews, dashboards, and AI-assisted insights across multiple organizational roles.

## 2. Repository Structure
- `backend/`: FastAPI service, business logic, DB models, migrations, tests
- `frontend/`: Next.js web application, UI components, state stores, API clients
- `docker-compose.yml`: Local multi-service stack definition
- `DEPLOYMENT.md`: Cloud deployment guidance

## 3. Implemented Features (Complete Inventory)

### 3.1 Platform and Security Foundations
- Async FastAPI backend with unified API response envelope middleware.
- Structured request logging middleware.
- Security headers middleware.
- CORS configuration from environment.
- Rate limiting via SlowAPI middleware.
- Global exception handlers for HTTP errors, validation errors, and unhandled server errors.
- Health check endpoint at `/health`.

### 3.2 Authentication, Identity, and Access Control
- Role-based login flow (`role`, `email`, `name`) with JWT token issuance.
- JWT claim model with `user_id`, `organization_id`, and `role`.
- Session bootstrap and current-user retrieval endpoints.
- RBAC support for Employee, Manager, HR, Leadership, and Admin.
- Role-aware route protection and unauthorized page handling on frontend.

### 3.3 Organization and User Management
- Organization creation and user assignment flows.
- User profile retrieval and update flows.
- Team and reporting views for managers.
- Employee master data management and manager mapping support.

### 3.4 Goal Management and Cascade
- Goal creation and editing.
- Goal listing and status tracking.
- Goal submission and manager approval flow.
- Goal assignment support.
- Goal cascade features to align team goals with org direction.
- KPI and objective data models for measurable performance plans.

### 3.5 Check-ins and Continuous Feedback
- Check-in scheduling and completion workflow.
- Check-in notes and attachments support.
- Check-in rating linkage.
- Employee and manager check-in views.

### 3.6 Ratings and Performance Reviews
- Performance rating creation and listing.
- Weighted score computation endpoint.
- Review generation and review analytics endpoints.
- Performance review data models and cycle association.

### 3.7 Dashboards and Analytics
- General dashboard endpoints.
- Manager dashboard endpoints and metrics surfaces.
- Employee dashboard endpoints (current + legacy compatibility dashboard).
- Leadership dashboard endpoints.
- HR dashboard endpoints.
- Reporting endpoints for aggregated views and exports.

### 3.8 Performance Cycles, Frameworks, and Forms
- Performance cycle CRUD flows.
- Active cycle discovery.
- Framework recommendation endpoint by role/department.
- Framework selection and annual operating plan related models.
- Dynamic forms endpoints for configurable workflow inputs.

### 3.9 AI Features
- AI goal suggestion flows.
- AI check-in summarization.
- AI review generation.
- AI feedback coaching.
- AI growth suggestion and training suggestion.
- AI decision insights for managers/leadership/HR.
- AI usage logging and limits enforcement by role.

### 3.10 Meetings and Google Integrations
- Google Calendar availability lookup.
- Meeting scheduling with Meet link creation.
- Meeting CRUD endpoints.
- Meeting transcript sync endpoint.
- Meeting analytics summary endpoint.
- Backend-managed OAuth token refresh flow for Google APIs.

### 3.11 Notifications and Communication
- Notification log model and notification router.
- Meeting proposal model and related communication workflows.

### 3.12 HR and Succession Features
- HR-specific routes and admin/people operations.
- Succession planning data model.
- Employee 9-box model for talent matrix workflows.

### 3.13 Frontend Application Features
- Next.js App Router-based route structure for role-specific sections.
- Implemented pages/routes include:
  - `/` and `/login` (authentication entry points)
  - `/dashboard`
  - `/manager` and `/manager-dashboard`
  - `/employee` and `/employee-dashboard`
  - `/hr` and `/hr-dashboard`
  - `/leadership`
  - `/goals`
  - `/checkins`
  - `/meetings`
  - `/reviews`
  - `/auth` callback handling routes
  - `/admin` section
  - `/unauthorized`
- Zustand-based client state stores for session/domain state.
- Service-layer API clients under `src/services`.
- Route middleware in `src/middleware.ts` for guarded navigation.

### 3.14 DevOps, Data, and Quality
- Alembic migration framework in `backend/migrations`.
- Seed SQL and mock data scripts in `backend/sql` and `backend/scripts`.
- Backend automated test suite under `backend/tests`.
- Dockerfiles for backend and frontend.
- Root Docker Compose for local multi-container orchestration.

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
# PMS Technical Documentation

## 1. Overview
This repository contains an AI-native Performance Management System (PMS) built with:
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL, Alembic
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand
- Integrations: Google Calendar / Google Meet, Gemini-based AI workflows

The platform supports goal setting, check-ins, ratings, reviews, dashboards, and AI-assisted insights across multiple organizational roles.

## 2. Repository Structure
- `backend/`: FastAPI service, business logic, DB models, migrations, tests
- `frontend/`: Next.js web application, UI components, state stores, API clients
- `docker-compose.yml`: Local multi-service stack definition
- `DEPLOYMENT.md`: Cloud deployment guidance

## 3. Implemented Features (Complete Inventory)

### 3.1 Platform and Security Foundations
- Async FastAPI backend with unified API response envelope middleware.
- Structured request logging middleware.
- Security headers middleware.
- CORS configuration from environment.
- Rate limiting via SlowAPI middleware.
- Global exception handlers for HTTP errors, validation errors, and unhandled server errors.
- Health check endpoint at `/health`.

### 3.2 Authentication, Identity, and Access Control
- Role-based login flow (`role`, `email`, `name`) with JWT token issuance.
- JWT claim model with `user_id`, `organization_id`, and `role`.
- Session bootstrap and current-user retrieval endpoints.
- RBAC support for Employee, Manager, HR, Leadership, and Admin.
- Role-aware route protection and unauthorized page handling on frontend.

### 3.3 Organization and User Management
- Organization creation and user assignment flows.
- User profile retrieval and update flows.
- Team and reporting views for managers.
- Employee master data management and manager mapping support.

### 3.4 Goal Management and Cascade
- Goal creation and editing.
- Goal listing and status tracking.
- Goal submission and manager approval flow.
- Goal assignment support.
- Goal cascade features to align team goals with org direction.
- KPI and objective data models for measurable performance plans.

### 3.5 Check-ins and Continuous Feedback
- Check-in scheduling and completion workflow.
- Check-in notes and attachments support.
- Check-in rating linkage.
- Employee and manager check-in views.

### 3.6 Ratings and Performance Reviews
- Performance rating creation and listing.
- Weighted score computation endpoint.
- Review generation and review analytics endpoints.
- Performance review data models and cycle association.

### 3.7 Dashboards and Analytics
- General dashboard endpoints.
- Manager dashboard endpoints and metrics surfaces.
- Employee dashboard endpoints (current + legacy compatibility dashboard).
- Leadership dashboard endpoints.
- HR dashboard endpoints.
- Reporting endpoints for aggregated views and exports.

### 3.8 Performance Cycles, Frameworks, and Forms
- Performance cycle CRUD flows.
- Active cycle discovery.
- Framework recommendation endpoint by role/department.
- Framework selection and annual operating plan related models.
- Dynamic forms endpoints for configurable workflow inputs.

### 3.9 AI Features
- AI goal suggestion flows.
- AI check-in summarization.
- AI review generation.
- AI feedback coaching.
- AI growth suggestion and training suggestion.
- AI decision insights for managers/leadership/HR.
- AI usage logging and limits enforcement by role.

### 3.10 Meetings and Google Integrations
- Google Calendar availability lookup.
- Meeting scheduling with Meet link creation.
- Meeting CRUD endpoints.
- Meeting transcript sync endpoint.
- Meeting analytics summary endpoint.
- Backend-managed OAuth token refresh flow for Google APIs.

### 3.11 Notifications and Communication
- Notification log model and notification router.
- Meeting proposal model and related communication workflows.

### 3.12 HR and Succession Features
- HR-specific routes and admin/people operations.
- Succession planning data model.
- Employee 9-box model for talent matrix workflows.

### 3.13 Frontend Application Features
- Next.js App Router-based route structure for role-specific sections.
- Implemented pages/routes include:
	- `/` and `/login` (authentication entry points)
	- `/dashboard`
	- `/manager` and `/manager-dashboard`
	- `/employee` and `/employee-dashboard`
	- `/hr` and `/hr-dashboard`
	- `/leadership`
	- `/goals`
	- `/checkins`
	- `/meetings`
	- `/reviews`
	- `/auth` callback handling routes
	- `/admin` section
	- `/unauthorized`
- Zustand-based client state stores for session/domain state.
- Service-layer API clients under `src/services`.
- Route middleware in `src/middleware.ts` for guarded navigation.

### 3.14 DevOps, Data, and Quality
- Alembic migration framework in `backend/migrations`.
- Seed SQL and mock data scripts in `backend/sql` and `backend/scripts`.
- Backend automated test suite under `backend/tests`.
- Dockerfiles for backend and frontend.
- Root Docker Compose for local multi-container orchestration.

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
