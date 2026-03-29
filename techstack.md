# Tech Stack Overview

This project is an AI-native Performance Management System with a FastAPI backend and a Next.js frontend.

## Architecture
- Frontend: Next.js web application for role-based PMS workflows.
- Backend: FastAPI REST APIs for auth, goals, check-ins, ratings, reviews, AI, meetings, HR dashboards, and employee management.
- Data: PostgreSQL as the primary database.
- Caching and rate-limit support: Redis.
- AI: Google Gemini integration for goal generation, summaries, coaching, and insights.
- Calendar and meetings: Google Calendar and Meet integrations.

## Backend Technologies
- Python 3.11+
- FastAPI 0.115.8
- Uvicorn 0.34.0
- SQLAlchemy 2.0.38 (async ORM)
- asyncpg 0.30.0 (PostgreSQL driver)
- Alembic 1.14.1 (migrations)
- Pydantic 2.10.6 and pydantic-settings 2.7.1
- python-jose 3.3.0 (JWT)
- slowapi 0.1.9 (rate limiting)
- redis 5.2.1 (cache and infra support)
- python-multipart 0.0.20
- email-validator 2.2.0

### AI and Google Integrations
- google-genai 1.8.0
- google-auth 2.38.0
- google-api-python-client 2.165.0
- google-auth-httplib2 0.2.0

### Backend Testing
- pytest 8.3.5
- pytest-asyncio 0.25.3

## Frontend Technologies
- Next.js 14.2.35
- React 18
- TypeScript 5
- Tailwind CSS 3.4.1
- PostCSS 8
- ESLint 8 with eslint-config-next 14.2.35

### Frontend State, Forms, and UI
- Zustand 5.0.11 (state management)
- React Hook Form 7.71.2
- Zod 4.3.6 and @hookform/resolvers 5.2.2
- Axios 1.13.6 (HTTP client)
- Framer Motion 12.36.0 (animations)
- Recharts 3.8.0 (charts)
- Lucide React 0.577.0 (icons)
- Sonner 2.0.7 (toasts)
- js-cookie 3.0.5 (token cookie handling)
- class-variance-authority 0.7.1, clsx 2.1.1, tailwind-merge 3.5.0 (styling utilities)

## Database and Migrations
- PostgreSQL 16 (Docker image)
- Alembic migration history under backend/migrations/versions
- Enum-driven domain model (roles, statuses, labels)

## Infrastructure and DevOps
- Docker Compose 3.9
- Services: db, redis, backend, frontend
- Containerized local development for full stack bootstrapping
- Backend and frontend both exposed on standard local ports:
  - Backend: 8000
  - Frontend: 3000

## Deployment Targets
- Frontend: Vercel
- Backend: Google Cloud Run

## Security and Auth
- JWT-based authentication with role claims
- RBAC for employee, manager, hr, leadership, and admin roles
- CORS configuration via environment variables

## Core Product Domains
- Authentication and role-based access control
- Goal lifecycle and submissions
- Check-ins and summaries
- Ratings and performance reviews
- AI copilots for goals, feedback, growth, training, and decision intelligence
- Meeting scheduling and calendar integration
- HR team monitoring dashboards
- Dedicated employee management hierarchy

## Why This Stack
- Fast API development with strong structure: FastAPI plus Pydantic and SQLAlchemy gives a clean separation of routers, services, schemas, and models, which keeps feature growth manageable.
- Scales from startup to production: PostgreSQL for reliable relational data, Redis for performance support, and Docker-based services for consistent environments across dev and deploy.
- AI-ready by design: Gemini integration is built into domain workflows (goals, summaries, coaching, insights) rather than bolted on as a separate experiment.
- Frontend productivity and UX quality: Next.js with TypeScript enables maintainable code, while Tailwind, Framer Motion, and component utilities support fast iteration on modern UI.
- Strong team workflow support: Zustand, React Hook Form, and Zod reduce boilerplate and improve reliability for state-heavy, form-heavy business features.
- Deployment-friendly architecture: Vercel plus Cloud Run cleanly separates frontend and backend concerns, making CI/CD and independent scaling straightforward.
- Security and access control first: JWT auth and role-based permissions are integrated early, which is essential for HR and performance management systems handling sensitive data.

## Open Source vs Paid (Corporate Usage)

### Open Source (No License Fee)
- Python, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, pytest, pytest-asyncio
- Next.js, React, TypeScript, Tailwind CSS, PostCSS, ESLint
- Zustand, React Hook Form, Zod, Axios, Framer Motion, Recharts, Lucide React, Sonner, js-cookie
- PostgreSQL and Redis (self-hosted)
- Docker and Docker Compose

Note: Open source means no software license fee, but infrastructure and operations still cost money in production.

### Paid or Usage-Based for Corporates
- Google Gemini API: paid based on model usage/tokens (after any free tier limits)
- Google Cloud Run: paid compute/network usage
- Vercel: team, pro, or enterprise plans are usually paid for production-grade corporate usage
- Managed PostgreSQL/Redis providers (if used): paid service plans
- Google Cloud project billing: often required for production API usage and higher quotas

### Hybrid Cases (Free to Start, Paid at Scale)
- Google Calendar and Meet integrations via Google APIs: SDKs are open source, but production usage may require cloud billing setup and enterprise workspace governance
- Self-hosted PostgreSQL/Redis are open source, while managed hosted variants are paid
