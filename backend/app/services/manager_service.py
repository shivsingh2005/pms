from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID
from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.enums import CheckinStatus, GoalStatus, UserRole
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User


class ManagerService:
    @staticmethod
    async def get_team_performance(current_user: User, db: AsyncSession) -> dict:
        team_members_subquery = (
            select(User.id)
            .where(
                User.manager_id == current_user.id,
                User.is_active.is_(True),
            )
            .subquery()
        )

        team_result = await db.execute(
            select(User.id, User.name)
            .where(User.id.in_(select(team_members_subquery.c.id)))
            .order_by(User.name.asc())
        )
        team_members = team_result.all()
        team_ids = [row[0] for row in team_members]
        team_name_map = {str(row[0]): row[1] for row in team_members}

        if not team_ids:
            return {
                "avg_progress": 0.0,
                "completed_goals": 0,
                "consistency": 0.0,
                "at_risk": 0,
                "trend": [],
                "distribution": [
                    {"label": "EE", "count": 0},
                    {"label": "DE", "count": 0},
                    {"label": "ME", "count": 0},
                    {"label": "SME", "count": 0},
                    {"label": "NI", "count": 0},
                ],
                "workload": [],
                "performers": {"top": [], "low": []},
                "insights": ["No direct reports found for this manager."],
            }

        goals_agg_result = await db.execute(
            select(
                func.coalesce(func.avg(Goal.progress), 0.0),
                func.coalesce(func.sum(case((Goal.progress >= 100, 1), else_=0)), 0),
            )
            .where(
                Goal.user_id.in_(select(team_members_subquery.c.id)),
                Goal.status != GoalStatus.rejected,
            )
        )
        avg_progress_raw, completed_goals_raw = goals_agg_result.one()
        avg_progress = round(float(avg_progress_raw or 0.0), 1)
        completed_goals = int(completed_goals_raw or 0)

        expected_checkins = max(len(team_ids) * 6, 1)
        total_checkins_result = await db.execute(
            select(func.count(Checkin.id)).where(
                Checkin.employee_id.in_(select(team_members_subquery.c.id)),
                Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]),
            )
        )
        total_checkins = int(total_checkins_result.scalar() or 0)
        consistency = round((total_checkins / expected_checkins) * 100.0, 1)

        per_employee_progress_result = await db.execute(
            select(
                Goal.user_id,
                func.coalesce(func.avg(Goal.progress), 0.0).label("avg_progress"),
            )
            .where(
                Goal.user_id.in_(select(team_members_subquery.c.id)),
                Goal.status != GoalStatus.rejected,
            )
            .group_by(Goal.user_id)
        )
        per_employee_progress = [
            {
                "employee_id": str(row[0]),
                "employee_name": team_name_map.get(str(row[0]), "Unknown"),
                "progress": round(float(row[1] or 0.0), 1),
            }
            for row in per_employee_progress_result.all()
        ]

        at_risk = sum(1 for row in per_employee_progress if row["progress"] < 40)

        week_bucket = func.date_trunc("week", Goal.created_at).label("week_bucket")
        trend_result = await db.execute(
            select(
                func.to_char(week_bucket, "IYYY-IW").label("week"),
                func.coalesce(func.avg(Goal.progress), 0.0).label("progress"),
            )
            .where(
                Goal.user_id.in_(select(team_members_subquery.c.id)),
                Goal.status != GoalStatus.rejected,
            )
            .group_by(week_bucket)
            .order_by(week_bucket.asc())
        )
        trend_rows = trend_result.all()
        trend = [
            {
                "week": row[0],
                "progress": round(float(row[1] or 0.0), 1),
            }
            for row in trend_rows[-8:]
        ]

        latest_rating_subquery = (
            select(
                Rating.employee_id,
                func.max(Rating.created_at).label("latest_created_at"),
            )
            .where(Rating.employee_id.in_(select(team_members_subquery.c.id)))
            .group_by(Rating.employee_id)
            .subquery()
        )

        latest_rating_result = await db.execute(
            select(Rating.rating_label, func.count(Rating.id))
            .join(
                latest_rating_subquery,
                (Rating.employee_id == latest_rating_subquery.c.employee_id)
                & (Rating.created_at == latest_rating_subquery.c.latest_created_at),
            )
            .group_by(Rating.rating_label)
        )
        label_counts = {str(row[0].value): int(row[1]) for row in latest_rating_result.all()}
        distribution = [
            {"label": "EE", "count": label_counts.get("EE", 0)},
            {"label": "DE", "count": label_counts.get("DE", 0)},
            {"label": "ME", "count": label_counts.get("ME", 0)},
            {"label": "SME", "count": label_counts.get("SME", 0)},
            {"label": "NI", "count": label_counts.get("NI", 0)},
        ]

        workload_result = await db.execute(
            select(
                Goal.user_id,
                func.coalesce(func.sum(Goal.weightage), 0.0).label("total_weightage"),
            )
            .where(
                Goal.user_id.in_(select(team_members_subquery.c.id)),
                Goal.status != GoalStatus.rejected,
            )
            .group_by(Goal.user_id)
        )
        workload = [
            {
                "employee_id": str(row[0]),
                "employee_name": team_name_map.get(str(row[0]), "Unknown"),
                "total_weightage": round(float(row[1] or 0.0), 1),
            }
            for row in workload_result.all()
        ]
        workload = sorted(workload, key=lambda row: row["employee_name"])

        top_performers = sorted(
            [row for row in per_employee_progress if row["progress"] > 80],
            key=lambda row: row["progress"],
            reverse=True,
        )[:5]
        low_performers = sorted(
            [row for row in per_employee_progress if row["progress"] < 40],
            key=lambda row: row["progress"],
        )[:5]

        insights: list[str] = [f"{at_risk} employees are at risk."]
        if len(trend) >= 2:
            delta = round(trend[-1]["progress"] - trend[0]["progress"], 1)
            if delta >= 0:
                insights.append(f"Team performance improved by {delta}% over the tracked period.")
            else:
                insights.append(f"Team performance declined by {abs(delta)}% over the tracked period.")

        return {
            "avg_progress": avg_progress,
            "completed_goals": completed_goals,
            "consistency": consistency,
            "at_risk": at_risk,
            "trend": trend,
            "distribution": distribution,
            "workload": workload,
            "performers": {
                "top": top_performers,
                "low": low_performers,
            },
            "insights": insights,
        }

    @staticmethod
    async def list_team(current_user: User, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(User)
            .where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
            )
            .order_by(User.name.asc())
        )
        team = list(result.scalars().all())
        team_ids = [member.id for member in team]

        workload_map: dict[str, float] = {}
        goals_count_map: dict[str, int] = {}
        progress_map: dict[str, float] = {}
        consistency_map: dict[str, float] = {}
        avg_final_rating_map: dict[str, float] = {}
        if team_ids:
            workload_result = await db.execute(
                select(
                    Goal.user_id,
                    func.coalesce(func.avg(Goal.progress), 0.0),
                    func.coalesce(func.sum(Goal.weightage), 0.0),
                    func.count(Goal.id),
                )
                .where(Goal.user_id.in_(team_ids), Goal.status != GoalStatus.rejected)
                .group_by(Goal.user_id)
            )
            for user_id, progress, workload, count in workload_result.all():
                progress_map[str(user_id)] = round(float(progress or 0.0), 1)
                workload_map[str(user_id)] = round(float(workload or 0.0), 1)
                goals_count_map[str(user_id)] = int(count or 0)

            consistency_result = await db.execute(
                select(
                    Checkin.employee_id,
                    func.count(Checkin.id),
                    func.coalesce(
                        func.sum(
                            case(
                                (Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                )
                .where(Checkin.employee_id.in_(team_ids))
                .group_by(Checkin.employee_id)
            )
            for user_id, total_checkins, completed_checkins in consistency_result.all():
                total = int(total_checkins or 0)
                completed = int(completed_checkins or 0)
                consistency_map[str(user_id)] = round((completed / total) * 100.0, 1) if total else 0.0

            rating_result = await db.execute(
                select(
                    CheckinRating.employee_id,
                    func.coalesce(func.avg(CheckinRating.rating), 0.0),
                )
                .where(CheckinRating.employee_id.in_(team_ids))
                .group_by(CheckinRating.employee_id)
            )
            for user_id, avg_rating in rating_result.all():
                avg_final_rating_map[str(user_id)] = round(float(avg_rating or 0.0), 2)

        payload: list[dict] = []
        for member in team:
            member_id = str(member.id)
            progress = progress_map.get(member_id, 0.0)
            payload.append(
                {
                    "id": member_id,
                    "name": member.name,
                    "role": member.title or member.role.value,
                    "department": member.department or "General",
                    "profile_avatar": member.profile_picture,
                    "goal_progress_percent": progress,
                    "status": "On Track" if progress >= 70 else "At Risk",
                    "current_workload": workload_map.get(member_id, 0.0),
                    "current_goals_count": goals_count_map.get(member_id, 0),
                    "consistency_percent": consistency_map.get(member_id, 0.0),
                    "avg_final_rating": avg_final_rating_map.get(member_id, 0.0),
                }
            )

        return payload

    @staticmethod
    async def inspect_employee(current_user: User, employee_id: str, db: AsyncSession) -> dict:
        try:
            employee_uuid = UUID(employee_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee id") from exc

        employee = await db.get(User, employee_uuid)
        if not employee or not employee.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if current_user.role == UserRole.manager and employee.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your direct report")

        if current_user.role != UserRole.admin and employee.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization access is not allowed")

        goals_result = await db.execute(select(Goal).where(Goal.user_id == employee.id).order_by(Goal.created_at.desc()))
        goals = list(goals_result.scalars().all())

        checkins_result = await db.execute(
            select(Checkin).where(Checkin.employee_id == employee.id).order_by(Checkin.meeting_date.desc())
        )
        checkins = list(checkins_result.scalars().all())

        reviews_result = await db.execute(
            select(PerformanceReview)
            .where(PerformanceReview.employee_id == employee.id)
            .order_by(PerformanceReview.cycle_year.desc(), PerformanceReview.cycle_quarter.desc())
            .limit(12)
        )
        reviews = list(reviews_result.scalars().all())

        ratings_result = await db.execute(
            select(Rating).where(Rating.employee_id == employee.id).order_by(Rating.created_at.desc())
        )
        ratings = list(ratings_result.scalars().all())

        workload = round(sum(goal.weightage for goal in goals if goal.status != GoalStatus.rejected), 1)
        completed = sum(1 for goal in goals if goal.status == GoalStatus.approved and goal.progress >= 100)
        progress = round((sum(goal.progress for goal in goals) / len(goals)) if goals else 0.0, 1)
        submitted_checkins = sum(1 for row in checkins if row.status.value in {"submitted", "reviewed"})
        consistency = round((submitted_checkins / len(checkins) * 100.0), 1) if checkins else 0.0
        last_checkin = checkins[0].created_at if checkins else None

        latest_review = reviews[0] if reviews else None
        strengths = [item.strip() for item in (latest_review.strengths.split(",") if latest_review and latest_review.strengths else []) if item.strip()]
        weaknesses = [item.strip() for item in (latest_review.weaknesses.split(",") if latest_review and latest_review.weaknesses else []) if item.strip()]
        growth_areas = [item.strip() for item in (latest_review.growth_areas.split(",") if latest_review and latest_review.growth_areas else []) if item.strip()]

        if not strengths:
            strengths.append("Consistent contribution to active goals")
        if not weaknesses:
            weaknesses.append("No explicit weaknesses captured yet")
        if not growth_areas:
            growth_areas.append("Build depth in role-specific execution")

        return {
            "employee_id": str(employee.id),
            "name": employee.name,
            "employee_name": employee.name,
            "role": employee.title or employee.role.value,
            "department": employee.department or "General",
            "email": employee.email,
            "progress": progress,
            "goals_completed": completed,
            "consistency": consistency,
            "last_checkin": last_checkin,
            "current_workload": workload,
            "goals": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "progress": item.progress,
                    "status": item.status.value,
                }
                for item in goals
            ],
            "checkins": [
                {
                    "id": str(item.id),
                    "meeting_date": item.created_at,
                    "summary": item.summary,
                    "notes": item.manager_feedback or item.next_steps or item.summary,
                }
                for item in checkins
            ],
            "ratings": [
                {
                    "id": str(item.id),
                    "rating": item.rating_label.value,
                    "comments": item.comments,
                    "created_at": item.created_at,
                }
                for item in ratings
            ],
            "performance_history": [
                {
                    "cycle_year": row.cycle_year,
                    "cycle_quarter": row.cycle_quarter,
                    "overall_rating": row.overall_rating,
                    "summary": row.summary,
                    "comments": row.growth_areas,
                }
                for row in reviews
            ],
            "ai_insights": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "growth_areas": growth_areas,
            },
        }
