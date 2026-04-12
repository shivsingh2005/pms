from __future__ import annotations

from collections import defaultdict
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import Checkin
from app.models.employee import Employee
from app.models.enums import CheckinStatus, GoalStatus, RatingLabel, UserRole
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User
from app.services.manager_seed_service import ManagerSeedService


class ManagerService:
    @staticmethod
    def _split_insight_text(value: str | None) -> list[str]:
        if not value:
            return []
        parts = [part.strip() for part in value.replace("\n", ",").split(",")]
        return [part for part in parts if part]

    @staticmethod
    async def _team_count(current_user: User, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count(User.id)).where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def _repair_manager_relationships(current_user: User, db: AsyncSession) -> int:
        repaired = 0

        # Keep mirrored employee records aligned with direct-report user rows.
        direct_report_ids_result = await db.execute(
            select(User.id).where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
        )
        direct_report_ids = list(direct_report_ids_result.scalars().all())
        if direct_report_ids:
            sync_mirror_result = await db.execute(
                update(Employee)
                .where(
                    Employee.id.in_(direct_report_ids),
                    Employee.manager_id != current_user.id,
                )
                .values(manager_id=current_user.id)
            )
            repaired += int(sync_mirror_result.rowcount or 0)

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
            adopted_count = int(adopt_users_result.rowcount or 0)
            repaired += adopted_count

            if adopted_count > 0:
                adopted_ids_result = await db.execute(
                    select(User.id).where(
                        User.manager_id == current_user.id,
                        User.organization_id == current_user.organization_id,
                        User.is_active.is_(True),
                        User.role == UserRole.employee,
                    )
                )
                adopted_ids = list(adopted_ids_result.scalars().all())
                if adopted_ids:
                    sync_adopted_result = await db.execute(
                        update(Employee)
                        .where(
                            Employee.id.in_(adopted_ids),
                            Employee.manager_id.is_(None),
                        )
                        .values(manager_id=current_user.id)
                    )
                    repaired += int(sync_adopted_result.rowcount or 0)

        return repaired

    @staticmethod
    async def _ensure_team_data(current_user: User, db: AsyncSession) -> None:
        repaired_count = await ManagerService._repair_manager_relationships(current_user, db)
        if repaired_count > 0:
            await db.commit()

        team_count = await ManagerService._team_count(current_user, db)
        if team_count > 0:
            return

        employee_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
        )
        employee_count = int(employee_count_result.scalar() or 0)
        target_team_size = min(10, employee_count) if employee_count > 0 else 10

        await ManagerSeedService.seed_manager_data(current_user, db, team_size=target_team_size)

    @staticmethod
    async def _fetch_team_members(current_user: User, db: AsyncSession) -> list[User]:
        await ManagerService._ensure_team_data(current_user, db)

        users_result = await db.execute(
            select(User).where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
        )
        return list(users_result.scalars().all())

    @staticmethod
    async def _team_metrics(member_ids: list, db: AsyncSession) -> dict:
        if not member_ids:
            return {
                "goals": {},
                "checkins": {},
                "ratings": {},
                "trend": [],
                "distribution": [],
            }

        goals_result = await db.execute(
            select(
                Goal.user_id,
                func.count(Goal.id),
                func.coalesce(func.avg(Goal.progress), 0.0),
                func.coalesce(func.sum(Goal.weightage), 0.0),
                func.count(Goal.id).filter(Goal.progress >= 100),
            )
            .where(
                Goal.user_id.in_(member_ids),
                Goal.status != GoalStatus.rejected,
            )
            .group_by(Goal.user_id)
        )

        checkins_result = await db.execute(
            select(
                Checkin.employee_id,
                func.count(Checkin.id),
                func.count(Checkin.id).filter(Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed])),
                func.max(Checkin.created_at),
            )
            .where(Checkin.employee_id.in_(member_ids))
            .group_by(Checkin.employee_id)
        )

        ratings_result = await db.execute(
            select(
                Rating.employee_id,
                func.coalesce(func.avg(Rating.rating), 0.0),
            )
            .where(Rating.employee_id.in_(member_ids))
            .group_by(Rating.employee_id)
        )

        week_start_expr = func.date_trunc("week", Checkin.created_at)
        week_trend_result = await db.execute(
            select(
                week_start_expr,
                func.coalesce(func.avg(Checkin.overall_progress), 0.0),
            )
            .where(Checkin.employee_id.in_(member_ids))
            .group_by(week_start_expr)
            .order_by(week_start_expr.asc())
        )

        distribution_result = await db.execute(
            select(Rating.rating_label, func.count(Rating.id))
            .where(Rating.employee_id.in_(member_ids))
            .group_by(Rating.rating_label)
        )

        goals_by_user = {}
        for row in goals_result.all():
            goals_by_user[row[0]] = {
                "goal_count": int(row[1] or 0),
                "avg_progress": float(row[2] or 0.0),
                "workload": float(row[3] or 0.0),
                "completed_goals": int(row[4] or 0),
            }

        checkins_by_user = {}
        for row in checkins_result.all():
            total = int(row[1] or 0)
            done = int(row[2] or 0)
            consistency = (float(done) / float(total) * 100.0) if total else 0.0
            checkins_by_user[row[0]] = {
                "total": total,
                "done": done,
                "consistency": consistency,
                "last_checkin": row[3].isoformat() if row[3] else None,
            }

        ratings_by_user = {}
        for row in ratings_result.all():
            ratings_by_user[row[0]] = float(row[1] or 0.0)

        trend = [
            {
                "week": row[0].date().isoformat() if row[0] is not None else "",
                "progress": round(float(row[1] or 0.0), 1),
            }
            for row in week_trend_result.all()
        ]

        label_to_count = defaultdict(int)
        for label, count in distribution_result.all():
            if label is None:
                continue
            label_to_count[str(label)] = int(count or 0)

        distribution = [
            {"label": RatingLabel.EE.value, "count": label_to_count.get(RatingLabel.EE.value, 0)},
            {"label": RatingLabel.DE.value, "count": label_to_count.get(RatingLabel.DE.value, 0)},
            {"label": RatingLabel.ME.value, "count": label_to_count.get(RatingLabel.ME.value, 0)},
            {"label": RatingLabel.SME.value, "count": label_to_count.get(RatingLabel.SME.value, 0)},
            {"label": RatingLabel.NI.value, "count": label_to_count.get(RatingLabel.NI.value, 0)},
        ]

        return {
            "goals": goals_by_user,
            "checkins": checkins_by_user,
            "ratings": ratings_by_user,
            "trend": trend,
            "distribution": distribution,
        }

    @staticmethod
    def _member_payload(member: User, goals: dict, checkins: dict, ratings: dict) -> dict:
        goal_row = goals.get(member.id, {})
        checkin_row = checkins.get(member.id, {})
        avg_progress = float(goal_row.get("avg_progress", 0.0))
        consistency = float(checkin_row.get("consistency", 0.0))

        return {
            "id": str(member.id),
            "name": member.name,
            "role": member.title or member.role.value,
            "department": member.department or "General",
            "profile_avatar": member.profile_picture,
            "goal_progress_percent": round(avg_progress, 1),
            "status": "On Track" if avg_progress >= 70 else "At Risk",
            "current_workload": round(float(goal_row.get("workload", 0.0)), 1),
            "current_goals_count": int(goal_row.get("goal_count", 0)),
            "consistency_percent": round(consistency, 1),
            "avg_final_rating": round(float(ratings.get(member.id, 0.0)), 2),
            "completed_goals": int(goal_row.get("completed_goals", 0)),
            "last_checkin": checkin_row.get("last_checkin"),
            "checkins_used": int(checkin_row.get("done", 0)),
            "checkins_total": max(5, int(checkin_row.get("total", 0))),
        }

    @staticmethod
    async def list_team(current_user: User, db: AsyncSession) -> list[dict]:
        team = await ManagerService._fetch_team_members(current_user, db)
        member_ids = [member.id for member in team]
        metrics = await ManagerService._team_metrics(member_ids, db)

        return [
            ManagerService._member_payload(member, metrics["goals"], metrics["checkins"], metrics["ratings"])
            for member in team
        ]

    @staticmethod
    async def inspect_employee(current_user: User, employee_id: UUID, db: AsyncSession) -> dict:
        employee_result = await db.execute(
            select(User).where(
                User.id == employee_id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
                User.manager_id == current_user.id,
            )
        )
        employee = employee_result.scalar_one_or_none()
        if employee is None:
            return {}

        goal_rows_result = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == employee.id,
                Goal.status != GoalStatus.rejected,
            )
            .order_by(Goal.updated_at.desc())
        )
        goal_rows = list(goal_rows_result.scalars().all())

        checkin_rows_result = await db.execute(
            select(Checkin)
            .where(Checkin.employee_id == employee.id)
            .order_by(Checkin.created_at.desc())
        )
        checkin_rows = list(checkin_rows_result.scalars().all())

        rating_rows_result = await db.execute(
            select(Rating)
            .where(Rating.employee_id == employee.id)
            .order_by(Rating.created_at.desc())
        )
        rating_rows = list(rating_rows_result.scalars().all())

        performance_rows_result = await db.execute(
            select(PerformanceReview)
            .where(PerformanceReview.employee_id == employee.id)
            .order_by(PerformanceReview.cycle_year.desc(), PerformanceReview.cycle_quarter.desc())
        )
        performance_rows = list(performance_rows_result.scalars().all())

        goals_completed = sum(1 for row in goal_rows if float(row.progress or 0.0) >= 100.0)
        avg_progress = (
            sum(float(row.progress or 0.0) for row in goal_rows) / len(goal_rows)
            if goal_rows
            else 0.0
        )

        checkins_done = sum(1 for row in checkin_rows if row.status in {CheckinStatus.submitted, CheckinStatus.reviewed})
        consistency = (float(checkins_done) / float(len(checkin_rows)) * 100.0) if checkin_rows else 0.0

        workload = sum(float(row.weightage or 0.0) for row in goal_rows)
        last_checkin = checkin_rows[0].created_at.isoformat() if checkin_rows else None

        strengths: list[str] = []
        weaknesses: list[str] = []
        growth_areas: list[str] = []
        for row in performance_rows:
            strengths.extend(ManagerService._split_insight_text(row.strengths))
            weaknesses.extend(ManagerService._split_insight_text(row.weaknesses))
            growth_areas.extend(ManagerService._split_insight_text(row.growth_areas))

        if not strengths:
            strengths = ["Consistent collaboration"]
        if not weaknesses:
            weaknesses = ["Limited recent review notes"]
        if not growth_areas:
            growth_areas = ["Expand cross-functional impact"]

        return {
            "employee_id": str(employee.id),
            "name": employee.name,
            "employee_name": employee.name,
            "role": employee.title or employee.role.value,
            "department": employee.department or "General",
            "email": employee.email,
            "progress": round(avg_progress, 1),
            "goals_completed": int(goals_completed),
            "consistency": round(consistency, 1),
            "last_checkin": last_checkin,
            "current_workload": round(workload, 1),
            "goals": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "progress": round(float(row.progress or 0.0), 1),
                    "status": row.status.value,
                }
                for row in goal_rows
            ],
            "checkins": [
                {
                    "id": str(row.id),
                    "meeting_date": (row.meeting_date or row.created_at).isoformat(),
                    "summary": row.summary,
                    "notes": row.manager_feedback,
                }
                for row in checkin_rows
            ],
            "ratings": [
                {
                    "id": str(row.id),
                    "rating": row.rating_label.value,
                    "comments": row.comments,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rating_rows
            ],
            "performance_history": [
                {
                    "cycle_year": int(row.cycle_year),
                    "cycle_quarter": int(row.cycle_quarter),
                    "overall_rating": float(row.overall_rating) if row.overall_rating is not None else None,
                    "summary": row.summary,
                    "comments": row.summary,
                }
                for row in performance_rows
            ],
            "ai_insights": {
                "strengths": strengths[:6],
                "weaknesses": weaknesses[:6],
                "growth_areas": growth_areas[:6],
            },
        }

    @staticmethod
    async def get_dashboard_payload(current_user: User, db: AsyncSession) -> dict:
        team_members = await ManagerService._fetch_team_members(current_user, db)
        member_ids = [member.id for member in team_members]
        metrics = await ManagerService._team_metrics(member_ids, db)

        team = [
            ManagerService._member_payload(member, metrics["goals"], metrics["checkins"], metrics["ratings"])
            for member in team_members
        ]
        team_size = len(team)

        avg_progress = (
            sum(float(member.get("goal_progress_percent", 0.0)) for member in team) / team_size
            if team_size
            else 0.0
        )
        avg_consistency = (
            sum(float(member.get("consistency_percent", 0.0)) for member in team) / team_size
            if team_size
            else 0.0
        )
        at_risk = sum(1 for member in team if member.get("status") == "At Risk")
        completed_goals = sum(int(member.get("completed_goals", 0)) for member in team)

        pending_approvals = 0
        if member_ids:
            pending_result = await db.execute(
                select(func.count(Goal.id)).where(
                    Goal.user_id.in_(member_ids),
                    Goal.status == GoalStatus.submitted,
                )
            )
            pending_approvals = int(pending_result.scalar() or 0)

        ranking_rows = sorted(
            [
                {
                    "name": member.get("name", "Unknown"),
                    "score": round(float(member.get("goal_progress_percent", 0.0)), 1),
                    "trend": "up" if float(member.get("goal_progress_percent", 0.0)) >= 70 else "flat" if float(member.get("goal_progress_percent", 0.0)) >= 40 else "down",
                }
                for member in team
            ],
            key=lambda row: row["score"],
            reverse=True,
        )

        rag_heatmap = [
            {
                "id": member.get("id"),
                "name": member.get("name", "Unknown"),
                "progress": round(float(member.get("goal_progress_percent", 0.0)), 1),
                "consistency": round(float(member.get("consistency_percent", 0.0)), 1),
                "intensity": "high" if float(member.get("goal_progress_percent", 0.0)) < 40 else "medium" if float(member.get("goal_progress_percent", 0.0)) < 70 else "low",
            }
            for member in team
        ]

        checkin_status = [
            {
                "employee_id": member.get("id"),
                "name": member.get("name", "Unknown"),
                "checkins_used": int(member.get("checkins_used", 0)),
                "checkins_total": int(member.get("checkins_total", 5)),
                "last_checkin": member.get("last_checkin"),
            }
            for member in team
        ]

        performers = [
            {
                "employee_id": member.get("id"),
                "employee_name": member.get("name", "Unknown"),
                "progress": round(float(member.get("goal_progress_percent", 0.0)), 1),
                "rating": round(float(member.get("avg_final_rating", 0.0)), 2),
                "consistency": round(float(member.get("consistency_percent", 0.0)), 1),
            }
            for member in team
        ]
        top_performers = sorted(performers, key=lambda row: row["progress"], reverse=True)[:3]
        low_performers = sorted(performers, key=lambda row: row["progress"])[:3]

        return {
            "team_size": team_size,
            "avg_performance": round(avg_progress, 1),
            "avg_progress": round(avg_progress, 1),
            "consistency": round(avg_consistency, 1),
            "at_risk": at_risk,
            "pending_approvals": pending_approvals,
            "completed_goals": completed_goals,
            "team": [
                {
                    "employee_id": member.get("id"),
                    "employee_name": member.get("name", "Unknown"),
                    "progress": round(float(member.get("goal_progress_percent", 0.0)), 1),
                    "rating": round(float(member.get("avg_final_rating", 0.0)), 2),
                    "consistency": round(float(member.get("consistency_percent", 0.0)), 1),
                    "department": member.get("department"),
                }
                for member in team
            ],
            "stack_ranking": ranking_rows,
            "rag_heatmap": rag_heatmap,
            "performance_trend": metrics["trend"][-8:],
            "rating_distribution": metrics["distribution"],
            "checkin_status": checkin_status,
            "top_performers": top_performers,
            "low_performers": low_performers,
            "insights": [
                f"{at_risk} team member(s) currently need attention.",
                f"Average team progress is {round(avg_progress, 1)}%.",
            ],
        }

    @staticmethod
    async def get_team_performance_payload(current_user: User, db: AsyncSession) -> dict:
        dashboard = await ManagerService.get_dashboard_payload(current_user, db)
        team = dashboard["team"]
        raw_team = await ManagerService.list_team(current_user, db)
        workload_map = {member.get("id"): float(member.get("current_workload", 0.0)) for member in raw_team}

        workload = [
            {
                "employee_id": row.get("employee_id"),
                "employee_name": row.get("employee_name", "Unknown"),
                "total_weightage": round(float(workload_map.get(row.get("employee_id"), 0.0)), 1),
            }
            for row in team
        ]

        return {
            "team_size": dashboard["team_size"],
            "avg_performance": dashboard["avg_performance"],
            "avg_progress": dashboard["avg_progress"],
            "completed_goals": dashboard["completed_goals"],
            "consistency": dashboard["consistency"],
            "at_risk": dashboard["at_risk"],
            "trend": dashboard["performance_trend"],
            "distribution": dashboard["rating_distribution"],
            "workload": workload,
            "performers": {
                "top": dashboard["top_performers"],
                "low": dashboard["low_performers"],
            },
            "top_performers": dashboard["top_performers"],
            "low_performers": dashboard["low_performers"],
            "team": dashboard["team"],
            "insights": dashboard["insights"],
        }

    @staticmethod
    async def get_stack_ranking_payload(
        current_user: User,
        db: AsyncSession,
        *,
        sort_by: Literal["progress", "rating", "consistency"] = "progress",
        order: Literal["asc", "desc"] = "desc",
        at_risk_only: bool = False,
        limit: int = 10,
    ) -> dict:
        team = await ManagerService.list_team(current_user, db)

        items = [
            {
                "employee_id": row.get("id"),
                "employee_name": row.get("name", "Unknown"),
                "progress": round(float(row.get("goal_progress_percent", 0.0)), 1),
                "rating": round(float(row.get("avg_final_rating", 0.0)), 2),
                "consistency": round(float(row.get("consistency_percent", 0.0)), 1),
            }
            for row in team
        ]

        if at_risk_only:
            items = [row for row in items if row["progress"] < 50 or row["rating"] <= 2.0]

        reverse = order != "asc"
        items = sorted(items, key=lambda row: row.get(sort_by, 0), reverse=reverse)

        sliced = items[: max(1, min(limit, 100))]
        ranked = []
        for index, row in enumerate(sliced, start=1):
            risk_level = "low"
            if row["progress"] < 40 or row["rating"] <= 2.0 or row["consistency"] < 50:
                risk_level = "high"
            elif row["progress"] < 70 or row["rating"] < 3.0 or row["consistency"] < 70:
                risk_level = "medium"

            ranked.append(
                {
                    "rank": index,
                    **row,
                    "risk_level": risk_level,
                }
            )

        return {
            "sort_by": sort_by,
            "order": order,
            "at_risk_only": at_risk_only,
            "total_considered": len(items),
            "items": ranked,
        }
