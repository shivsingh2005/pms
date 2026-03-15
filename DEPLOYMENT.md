# Production Deployment Guide

## Architecture
- Frontend: Next.js on Vercel
- Backend: FastAPI on Google Cloud Run
- Database: Managed PostgreSQL (Cloud SQL / RDS / Neon)
- Cache: Redis (Cloud Memorystore / Upstash)

## 1) Environment Variables

### Backend
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `GOOGLE_CALENDAR_SCOPES`
- `GEMINI_API_KEY`
- `REDIS_URL`
- `CORS_ALLOW_ORIGINS`

### Frontend
- `NEXT_PUBLIC_API_BASE_URL`

## 2) Backend on Cloud Run
1. Build and push image:
   - `gcloud builds submit --tag gcr.io/<PROJECT_ID>/pms-backend ./backend`
2. Deploy:
   - `gcloud run deploy pms-backend --image gcr.io/<PROJECT_ID>/pms-backend --platform managed --allow-unauthenticated --region <REGION>`
3. Set env vars in Cloud Run service.
4. Point `DATABASE_URL` to managed Postgres with SSL settings.
5. Run Alembic migration job:
   - `alembic -c migrations/alembic.ini upgrade head`

## 3) Frontend on Vercel
1. Import `frontend` project in Vercel.
2. Set env vars:
   - `NEXT_PUBLIC_API_BASE_URL=https://<backend-url>/api/v1`
3. Deploy from `main` branch.

## 4) Database (Managed PostgreSQL)
- Enable automated backups
- Enforce SSL
- Restrict inbound access by network/service account
- Monitor slow queries and add indexes as needed

## 5) Cache (Redis)
- Use managed Redis
- Configure `REDIS_URL`
- Set alerting on memory and evictions

## 6) Local Full Stack
Use docker compose from repo root:

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379
