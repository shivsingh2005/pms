# AI-Native PMS Frontend

Modern Next.js 14 frontend for the PMS backend (FastAPI + role-based login + RBAC + AI + Calendar/Meet).

## Stack
- Next.js 14 App Router + TypeScript
- TailwindCSS + shadcn-style UI primitives
- Zustand state stores
- Axios service layer
- React Hook Form + Zod validation
- Recharts (analytics)
- Lucide icons
- Framer Motion animations
- Sonner toasts

## Setup
1. Copy `.env.example` to `.env.local`
2. Set:
   - `NEXT_PUBLIC_API_BASE_URL`
3. Run:

```bash
npm install
npm run dev
```

## Implemented Pages
- `/` Login (role + email + name)
- `/dashboard` Role-based dashboards
- `/goals` Goal creation, progress cards, vertical timeline
- `/checkins` Check-in scheduling, notes, AI summary area
- `/meetings` Google Calendar/Meet scheduling and timeline
- `/reviews` Performance review summaries

## Architecture
- `src/services` API layer (`api`, `auth`, `goals`, `checkins`, `meetings`, `reviews`, `ai`)
- `src/store` Zustand stores (`session`, `goals`, `meetings`, `ai`)
- `src/components` reusable UI + dashboard/goals/meetings/ai components
- `src/hooks/useAuthBootstrap.ts` session bootstrap from cookie + `/auth/me`

## Auth Flow
- Role payload from frontend login
- POST `/auth/role-login`
- JWT stored in secure cookie (`pms_token`)
- GET `/auth/me` bootstraps role-aware UI

## Notes
- Meetings endpoints require `X-Google-Access-Token` header from calendar connect flow.
- AI chat widget uses `POST /ai/chat` and shows safe fallback text when unavailable.
