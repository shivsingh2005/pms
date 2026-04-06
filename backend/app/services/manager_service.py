import logging

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID
from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.employee import Employee
from app.models.enums import CheckinStatus, GoalStatus, UserRole
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User
from app.services.manager_seed_service import ManagerSeedService


class ManagerService:
    logger = logging.getLogger(__name__)

    @staticmethod
    async def _team_count(current_user: User, db: AsyncSession) -> int:
        team_count_stmt = select(func.count(User.id)).where(
            User.manager_id == current_user.id,
            User.organization_id == current_user.organization_id,
            User.is_active.is_(True),
            User.role == UserRole.employee,
        )
        team_count_result = await db.execute(team_count_stmt)
        return int(team_count_result.scalar() or 0)

    @staticmethod
    async def _repair_manager_relationships(current_user: User, db: AsyncSession) -> int:
        repaired = 0

        # Bring User.manager_id back in sync when employee mirror rows already point to this manager.
        mirrored_employee_ids_result = await db.execute(
            select(Employee.id).where(
                Employee.manager_id == current_user.id,
                Employee.is_active.is_(True),
            )
        )
        mirrored_employee_ids = list(mirrored_employee_ids_result.scalars().all())
        if mirrored_employee_ids:
            sync_users_result = await db.execute(
                update(User)
                .where(
                    User.id.in_(mirrored_employee_ids),
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                    User.role == UserRole.employee,
                    User.manager_id.is_distinct_from(current_user.id),
                )
                .values(manager_id=current_user.id)
            )
            repaired += int(sync_users_result.rowcount or 0)

        # If this manager still has no team, adopt orphan employees in the same organization.
        if await ManagerService._team_count(current_user, db) == 0:
            adopt_users_result = await db.execute(
                update(User)
                .where(
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                    User.role == UserRole.employee,
                    User.manager_id.is_(None),
                )
                .values(manager_id=current_user.id)
            )
            repaired += int(adopt_users_result.rowcount or 0)

            adopted_user_ids_result = await db.execute(
                select(User.id).where(
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                    User.role == UserRole.employee,
                    User.manager_id == current_user.id,
                )
            )
            adopted_user_ids = list(adopted_user_ids_result.scalars().all())
            if adopted_user_ids:
                sync_employee_rows_result = await db.execute(
                    update(Employee)
                    .where(
                        Employee.id.in_(adopted_user_ids),
                        Employee.manager_id.is_(None),
                    )
                    .values(manager_id=current_user.id)
                )
                repaired += int(sync_employee_rows_result.rowcount or 0)

        return repaired

    @staticmethod
    async def _ensure_team_data(current_user: User, db: AsyncSession) -> None:
        repaired_count = await ManagerService._repair_manager_relationships(current_user, db)
        if repaired_count > 0:
            await db.commit()
            ManagerService.logger.info(
                "Manager relationship repair executed",
                extra={"manager_id": str(current_user.id), "repaired_records": repaired_count},
            )

        team_count = await ManagerService._team_count(current_user, db)
        if team_count > 0:
            team_ids_subquery = select(User.id).where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
            )

            goal_count_result = await db.execute(select(func.count(Goal.id)).where(Goal.user_id.in_(team_ids_subquery)))
            checkin_count_result = await db.execute(select(func.count(Checkin.id)).where(Checkin.employee_id.in_(team_ids_subquery)))
            rating_count_result = await db.execute(select(func.count(Rating.id)).where(Rating.employee_id.in_(team_ids_subquery)))
            checkin_rating_count_result = await db.execute(
                select(func.count(CheckinRating.id)).where(CheckinRating.employee_id.in_(team_ids_subquery))
            )
            meeting_count_result = await db.execute(select(func.count(Meeting.id)).where(Meeting.employee_id.in_(team_ids_subquery)))

            goal_count = int(goal_count_result.scalar() or 0)
            checkin_count = int(checkin_count_result.scalar() or 0)
            rating_count = int(rating_count_result.scalar() or 0)
            checkin_rating_count = int(checkin_rating_count_result.scalar() or 0)
            meeting_count = int(meeting_count_result.scalar() or 0)

            if min(goal_count, checkin_count, rating_count, checkin_rating_count, meeting_count) == 0:
                seeded = await ManagerSeedService.seed_activity_for_existing_team(current_user, db)
                ManagerService.logger.info(
                    "Manager dashboard team activity auto-seeded",
                    extra={
                        "manager_id": str(current_user.id),
                        "seeded_records": seeded,
                        "goal_count": goal_count,
                        "checkin_count": checkin_count,
                        "rating_count": rating_count,
                        "checkin_rating_count": checkin_rating_count,
                        "meeting_count": meeting_count,
                    },
                )
            return

        employee_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
        )
        employee_count = int(employee_count_result.scalar() or 0)

        created = await ManagerSeedService.seed_manager_data(current_user, db, team_size=10)
        ManagerService.logger.info(
            "Manager dashboard auto-seed executed",
            extra={
                "manager_id": str(current_user.id),
                "created_team_members": created,
                "organization_employee_count": employee_count,
            },
        )

    @staticmethod
    async def get_team_performance(current_user: User, db: AsyncSession) -> dict:
        await ManagerService._ensure_team_data(current_user, db)

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

        ManagerService.logger.info(
            "Manager dashboard team fetched",
            extra={"manager_id": str(current_user.id), "team_size": len(team_ids)},
        )

        if not team_ids:
            return {
                "team_size": 0,
                "avg_performance": 0.0,
                "avg_progress": 0.0,
                "completed_goals": 0,
                "consistency": 0.0,
                "at_risk": 0,
                "message": "No team assigned",
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
                "top_performers": [],
                "low_performers": [],
                "team": [],
                "insights": ["No direct reports found for this manager."],
            }

        avg_performance_result = await db.execute(
            select(func.coalesce(func.avg(CheckinRating.rating), 0.0)).where(
                CheckinRating.employee_id.in_(select(team_members_subquery.c.id))
            )
        )
        avg_performance = round(float(avg_performance_result.scalar() or 0.0), 2)

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
        consistency = round(min((total_checkins / expected_checkins) * 100.0, 100.0), 1)

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

        per_employee_rating_result = await db.execute(
            select(
                CheckinRating.employee_id,
                func.coalesce(func.avg(CheckinRating.rating), 0.0).label("avg_rating"),
            )
            .where(CheckinRating.employee_id.in_(select(team_members_subquery.c.id)))
            .group_by(CheckinRating.employee_id)
        )
        per_employee_rating_map = {
            str(row[0]): round(float(row[1] or 0.0), 2)
            for row in per_employee_rating_result.all()
        }

        checkin_consistency_result = await db.execute(
            select(
                Checkin.employee_id,
                func.count(Checkin.id).label("total"),
                func.coalesce(
                    func.sum(
                        case(
                            (Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("completed"),
            )
            .where(Checkin.employee_id.in_(select(team_members_subquery.c.id)))
            .group_by(Checkin.employee_id)
        )
        per_employee_consistency_map: dict[str, float] = {}
        for employee_id, total, completed in checkin_consistency_result.all():
            total_count = int(total or 0)
            completed_count = int(completed or 0)
            per_employee_consistency_map[str(employee_id)] = (
                round((completed_count / total_count) * 100.0, 1) if total_count else 0.0
            )

        progress_map = {row["employee_id"]: row["progress"] for row in per_employee_progress}
        team_snapshot = [
            {
                "employee_id": employee_id,
                "employee_name": team_name_map.get(employee_id, "Unknown"),
                "progress": progress_map.get(employee_id, 0.0),
                "rating": per_employee_rating_map.get(employee_id, 0.0),
                "consistency": per_employee_consistency_map.get(employee_id, 0.0),
            }
            for employee_id in [str(team_id) for team_id in team_ids]
        ]

        at_risk = sum(1 for row in team_snapshot if row["progress"] < 50 or row["rating"] <= 2)

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

        top_performers = sorted(team_snapshot, key=lambda row: row["progress"], reverse=True)[:3]
        low_performers = sorted(team_snapshot, key=lambda row: row["progress"])[:3]

        insights: list[str] = [f"{at_risk} employees are at risk."]
        if len(trend) >= 2:
            delta = round(trend[-1]["progress"] - trend[0]["progress"], 1)
            if delta >= 0:
                insights.append(f"Team performance improved by {delta}% over the tracked period.")
            else:
                insights.append(f"Team performance declined by {abs(delta)}% over the tracked period.")

        return {
            "team_size": len(team_ids),
            "avg_performance": avg_performance,
            "avg_progress": avg_progress,
            "completed_goals": completed_goals,
            "consistency": consistency,
            "at_risk": at_risk,
            "message": None,
            "trend": trend,
            "distribution": distribution,
            "workload": workload,
            "performers": {
                "top": top_performers,
                "low": low_performers,
            },
            "top_performers": top_performers,
            "low_performers": low_performers,
            "team": team_snapshot,
            "insights": insights,
        }

    @staticmethod
    async def get_stack_ranking(
        current_user: User,
        db: AsyncSession,
        *,
        sort_by: str = "progress",
        order: str = "desc",
        at_risk_only: bool = False,
        limit: int = 10,
    ) -> dict:
        payload = await ManagerService.get_team_performance(current_user, db)
        rows = list(payload.get("team", []))

        def risk_level(row: dict) -> str:
            progress = float(row.get("progress", 0.0) or 0.0)
            rating = float(row.get("rating", 0.0) or 0.0)
            consistency = float(row.get("consistency", 0.0) or 0.0)
            if progress < 40 or rating <= 2 or consistency < 50:
                return "high"
            if progress < 60 or rating <= 3 or consistency < 70:
                return "medium"
            return "low"

        enriched: list[dict] = []
        for row in rows:
            enriched.append(
                {
                    "employee_id": row.get("employee_id"),
                    "employee_name": row.get("employee_name", "Unknown"),
                    "progress": round(float(row.get("progress", 0.0) or 0.0), 1),
                    "rating": round(float(row.get("rating", 0.0) or 0.0), 2),
                    "consistency": round(float(row.get("consistency", 0.0) or 0.0), 1),
                    "risk_level": risk_level(row),
                }
            )

        if at_risk_only:
            enriched = [row for row in enriched if row["risk_level"] in {"high", "medium"}]

        safe_sort_by = sort_by if sort_by in {"progress", "rating", "consistency"} else "progress"
        reverse = order != "asc"
        enriched.sort(key=lambda row: (row[safe_sort_by], row["progress"], row["rating"]), reverse=reverse)

        trimmed = enriched[: max(1, min(limit, 100))]
        items = [
            {
                "rank": idx,
                **row,
            }
            for idx, row in enumerate(trimmed, start=1)
        ]

        return {
            "sort_by": safe_sort_by,
            "order": "asc" if order == "asc" else "desc",
            "at_risk_only": at_risk_only,
            "total_considered": len(enriched),
            "items": items,
        }

    @staticmethod
    async def list_team(current_user: User, db: AsyncSession) -> list[dict]:
        await ManagerService._ensure_team_data(current_user, db)

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

        if employee.organization_id != current_user.organization_id:
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
                    "notes": item.manager_feedback or item.achievements or item.summary,
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
