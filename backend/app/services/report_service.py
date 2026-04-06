from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ai_service import AIService
from app.models.checkin import Checkin
from app.models.enums import UserRole
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User


class ReportService:
    @staticmethod
    async def _assert_scope_access(current_user: User, report_type: str, employee_id: str | None, manager_id: str | None) -> None:
        role = current_user.role
        if role == UserRole.manager and report_type == "business":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot generate business reports")
        if role == UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees cannot generate reports")
        if report_type == "individual" and not employee_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="employee_id is required for individual report")
        if report_type == "team" and role == UserRole.manager and manager_id and manager_id != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can generate only own team reports")

    @staticmethod
    async def generate(current_user: User, report_type: str, employee_id: str | None, manager_id: str | None, db: AsyncSession) -> dict:
        await ReportService._assert_scope_access(current_user, report_type, employee_id, manager_id)

        scope_user_ids: list[UUID] = []
        if report_type == "individual" and employee_id:
            try:
                scope_user_ids = [UUID(employee_id)]
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee_id") from exc
        elif report_type == "team":
            manager_uuid = current_user.id
            if manager_id:
                try:
                    manager_uuid = UUID(manager_id)
                except ValueError as exc:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manager_id") from exc
            members_result = await db.execute(
                select(User.id).where(
                    User.manager_id == manager_uuid,
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                )
            )
            scope_user_ids = list(members_result.scalars().all())
        else:
            users_result = await db.execute(
                select(User.id).where(
                    User.organization_id == current_user.organization_id,
                    User.role == UserRole.employee,
                    User.is_active.is_(True),
                )
            )
            scope_user_ids = list(users_result.scalars().all())

        if not scope_user_ids:
            return {
                "report_type": report_type,
                "generated_at": datetime.now(timezone.utc),
                "summary": "No records found for selected scope.",
                "sections": [],
                "metadata": {"employee_count": 0},
            }

        goals_result = await db.execute(select(Goal.title, Goal.progress).where(Goal.user_id.in_(scope_user_ids)).limit(200))
        checkins_result = await db.execute(select(Checkin.summary).where(Checkin.employee_id.in_(scope_user_ids)).limit(200))
        ratings_result = await db.execute(select(func.avg(Rating.rating), func.count(Rating.id)).where(Rating.employee_id.in_(scope_user_ids)))
        reviews_result = await db.execute(select(PerformanceReview.summary).where(PerformanceReview.employee_id.in_(scope_user_ids)).limit(100))

        goal_rows = goals_result.all()
        checkin_notes = [row for row in checkins_result.scalars().all() if row]
        review_summaries = [row for row in reviews_result.scalars().all() if row]
        avg_rating, ratings_count = ratings_result.one()

        ai = AIService()
        narrative = await ai.generate_performance_review(
            user=current_user,
            employee_goals=[f"{title} ({round(float(progress or 0), 1)}%)" for title, progress in goal_rows] or ["No goals found"],
            checkin_notes=checkin_notes or ["No check-ins found"],
            manager_comments="Generate concise executive report narrative.",
            db=db,
        )

        sections = [
            {
                "heading": "Executive Summary",
                "content": [narrative.get("performance_summary", "Summary unavailable")],
            },
            {
                "heading": "Strengths",
                "content": list(narrative.get("strengths", [])),
            },
            {
                "heading": "Development Areas",
                "content": list(narrative.get("weaknesses", [])),
            },
            {
                "heading": "Growth Plan",
                "content": list(narrative.get("growth_plan", [])),
            },
        ]

        if review_summaries:
            sections.append({
                "heading": "Review Themes",
                "content": review_summaries[:5],
            })

        return {
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc),
            "summary": narrative.get("performance_summary", "Summary unavailable"),
            "sections": sections,
            "metadata": {
                "employee_count": len(scope_user_ids),
                "goals_count": len(goal_rows),
                "ratings_count": int(ratings_count or 0),
                "avg_rating": round(float(avg_rating or 0.0), 2),
            },
        }
