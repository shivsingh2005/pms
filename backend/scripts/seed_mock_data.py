from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone, date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.goal import Goal
from app.models.checkin import Checkin
from app.models.rating import Rating
from app.models.performance_review import PerformanceReview
from app.models.performance_cycle import PerformanceCycle
from app.models.enums import UserRole, GoalStatus, GoalFramework, CheckinStatus, RatingLabel


ORG_ID = UUID("11111111-1111-1111-1111-111111111111")

USERS = [
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "google_id": "seed-lead-0",
        "email": "executive@acmepms.com",
        "name": "Arjun Mehta",
        "role": UserRole.leadership,
        "manager_id": None,
        "department": "Executive",
        "title": "Executive Director",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
        "google_id": "seed-hr-1",
        "email": "hr@acmepms.com",
        "name": "Nisha Verma",
        "role": UserRole.hr,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "department": "HR",
        "title": "HRBP",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
        "google_id": "seed-mgr-1",
        "email": "manager.eng@acmepms.com",
        "name": "Priya Iyer",
        "role": UserRole.manager,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "department": "Engineering",
        "title": "Engineering Manager",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
        "google_id": "seed-mgr-2",
        "email": "manager.sales@acmepms.com",
        "name": "Meera Nair",
        "role": UserRole.manager,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "department": "Sales",
        "title": "Sales Manager",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
        "google_id": "seed-emp-1",
        "email": "shiv@acmepms.com",
        "name": "Shiv Menon",
        "role": UserRole.employee,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
        "department": "Engineering",
        "title": "Backend Developer",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6"),
        "google_id": "seed-emp-2",
        "email": "ritika@acmepms.com",
        "name": "Ritika Das",
        "role": UserRole.employee,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
        "department": "Engineering",
        "title": "Frontend Developer",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7"),
        "google_id": "seed-emp-3",
        "email": "kavya@acmepms.com",
        "name": "Kavya Sen",
        "role": UserRole.employee,
        "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
        "department": "Sales",
        "title": "Sales Executive",
    },
    {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa8"),
        "google_id": "seed-lead-1",
        "email": "leadership@acmepms.com",
        "name": "Devansh Malhotra",
        "role": UserRole.leadership,
        "manager_id": None,
        "department": "Executive",
        "title": "Business Head",
    },
]


async def _upsert_org(db: AsyncSession) -> None:
    existing = await db.get(Organization, ORG_ID)
    if not existing:
        db.add(Organization(id=ORG_ID, name="AcmePMS", domain="acmepms.com"))


async def _upsert_users(db: AsyncSession) -> None:
    for row in USERS:
        user = await db.get(User, row["id"])
        if not user:
            db.add(
                User(
                    id=row["id"],
                    google_id=row["google_id"],
                    email=row["email"],
                    name=row["name"],
                    profile_picture=None,
                    role=row["role"],
                    organization_id=ORG_ID,
                    manager_id=row["manager_id"],
                    department=row["department"],
                    title=row["title"],
                    is_active=True,
                )
            )


async def _insert_if_missing(db: AsyncSession, model, record_id: UUID, payload: dict) -> None:
    existing = await db.get(model, record_id)
    if not existing:
        db.add(model(id=record_id, **payload))


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        await _upsert_org(db)
        await _upsert_users(db)

        await _insert_if_missing(
            db,
            PerformanceCycle,
            UUID("22222222-2222-2222-2222-222222222222"),
            {
                "organization_id": ORG_ID,
                "name": "FY2026 Q2",
                "cycle_type": "quarterly",
                "framework": "OKR",
                "start_date": date(2026, 4, 1),
                "end_date": date(2026, 6, 30),
                "goal_setting_deadline": date(2026, 4, 20),
                "self_review_deadline": date(2026, 6, 25),
                "checkin_cap_per_quarter": 5,
                "ai_usage_cap_per_quarter": 3,
                "is_active": True,
            },
        )

        await _insert_if_missing(
            db,
            Goal,
            UUID("33333333-3333-3333-3333-333333333331"),
            {
                "user_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "title": "Improve API response time",
                "description": "Reduce p95 latency across core endpoints.",
                "weightage": 30,
                "status": GoalStatus.approved,
                "progress": 82,
                "framework": GoalFramework.OKR,
            },
        )
        await _insert_if_missing(
            db,
            Goal,
            UUID("33333333-3333-3333-3333-333333333332"),
            {
                "user_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "title": "Increase test coverage",
                "description": "Raise service coverage for critical paths.",
                "weightage": 25,
                "status": GoalStatus.approved,
                "progress": 76,
                "framework": GoalFramework.OKR,
            },
        )
        await _insert_if_missing(
            db,
            Goal,
            UUID("33333333-3333-3333-3333-333333333333"),
            {
                "user_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6"),
                "title": "Improve frontend performance",
                "description": "Reduce LCP and CLS for dashboard screens.",
                "weightage": 35,
                "status": GoalStatus.approved,
                "progress": 88,
                "framework": GoalFramework.OKR,
            },
        )
        await _insert_if_missing(
            db,
            Goal,
            UUID("33333333-3333-3333-3333-333333333334"),
            {
                "user_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7"),
                "title": "Pipeline coverage growth",
                "description": "Grow qualified opportunities for Q2.",
                "weightage": 40,
                "status": GoalStatus.approved,
                "progress": 72,
                "framework": GoalFramework.MBO,
            },
        )

        now = datetime.now(timezone.utc)
        await _insert_if_missing(
            db,
            Checkin,
            UUID("44444444-4444-4444-4444-444444444441"),
            {
                "goal_ids": [UUID("33333333-3333-3333-3333-333333333331")],
                "goal_updates": [{"goal_id": "33333333-3333-3333-3333-333333333331", "progress": 82, "note": "API latency update"}],
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "meeting_date": now - timedelta(days=20),
                "status": CheckinStatus.reviewed,
                "transcript": "Discussed optimization progress.",
                "summary": "Good progress on API latency.",
                "achievements": "Reduced p95 query latency in core endpoints.",
                "meeting_link": None,
                "created_at": now - timedelta(days=20),
                "overall_progress": 82,
                "blockers": None,
                "confidence_level": 4,
            },
        )
        await _insert_if_missing(
            db,
            Checkin,
            UUID("44444444-4444-4444-4444-444444444442"),
            {
                "goal_ids": [UUID("33333333-3333-3333-3333-333333333332")],
                "goal_updates": [{"goal_id": "33333333-3333-3333-3333-333333333332", "progress": 76, "note": "Test roadmap update"}],
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "meeting_date": now - timedelta(days=10),
                "status": CheckinStatus.reviewed,
                "transcript": "Reviewed testing roadmap.",
                "summary": "Coverage improving with integration test plan.",
                "achievements": "Expanded integration test matrix for critical services.",
                "meeting_link": None,
                "created_at": now - timedelta(days=10),
                "overall_progress": 76,
                "blockers": None,
                "confidence_level": 4,
            },
        )
        await _insert_if_missing(
            db,
            Checkin,
            UUID("44444444-4444-4444-4444-444444444443"),
            {
                "goal_ids": [UUID("33333333-3333-3333-3333-333333333334")],
                "goal_updates": [{"goal_id": "33333333-3333-3333-3333-333333333334", "progress": 72, "note": "Pipeline update"}],
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
                "meeting_date": now + timedelta(days=3),
                "status": CheckinStatus.submitted,
                "transcript": None,
                "summary": "Pipeline progressing with pending external sign-off.",
                "achievements": "Improved lead pipeline quality baseline.",
                "meeting_link": None,
                "created_at": now,
                "overall_progress": 72,
                "blockers": "Awaiting client sign-off for Q2 pipeline targets.",
                "confidence_level": 3,
            },
        )

        await _insert_if_missing(
            db,
            Rating,
            UUID("55555555-5555-5555-5555-555555555551"),
            {
                "goal_id": UUID("33333333-3333-3333-3333-333333333331"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "rating": 4,
                "rating_label": RatingLabel.DE,
                "comments": "Strong execution and measurable impact.",
                "created_at": now,
            },
        )
        await _insert_if_missing(
            db,
            Rating,
            UUID("55555555-5555-5555-5555-555555555552"),
            {
                "goal_id": UUID("33333333-3333-3333-3333-333333333333"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6"),
                "rating": 5,
                "rating_label": RatingLabel.EE,
                "comments": "Exceeded expectations on performance improvements.",
                "created_at": now,
            },
        )
        await _insert_if_missing(
            db,
            Rating,
            UUID("55555555-5555-5555-5555-555555555553"),
            {
                "goal_id": UUID("33333333-3333-3333-3333-333333333334"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7"),
                "rating": 3,
                "rating_label": RatingLabel.ME,
                "comments": "Good pipeline increase but conversion needs work.",
                "created_at": now,
            },
        )

        await _insert_if_missing(
            db,
            PerformanceReview,
            UUID("66666666-6666-6666-6666-666666666661"),
            {
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "cycle_year": 2026,
                "cycle_quarter": 1,
                "overall_rating": 3.8,
                "summary": "Consistent backend delivery with quality improvements.",
                "strengths": "Execution and collaboration",
                "weaknesses": "Long-tail bug prevention",
                "growth_areas": "Architecture and observability",
                "created_at": now,
            },
        )
        await _insert_if_missing(
            db,
            PerformanceReview,
            UUID("66666666-6666-6666-6666-666666666662"),
            {
                "employee_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6"),
                "manager_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
                "cycle_year": 2026,
                "cycle_quarter": 1,
                "overall_rating": 4.3,
                "summary": "Strong frontend outcomes and measurable UX wins.",
                "strengths": "Ownership and quality",
                "weaknesses": "Dependency management",
                "growth_areas": "Performance optimization",
                "created_at": now,
            },
        )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
    print("Mock data seed completed.")
