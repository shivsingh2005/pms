from collections import defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.checkin import Checkin
from app.models.enums import CheckinStatus, RatingLabel, UserRole
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User


class DashboardService:
    @staticmethod
    def _bucket_readiness(score: float) -> str:
        if score >= 80:
            return "High"
        if score >= 50:
            return "Medium"
        return "Low"

    @staticmethod
    async def _rating_distribution(filter_clause, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(Rating.rating_label, func.count(Rating.id))
            .where(filter_clause)
            .group_by(Rating.rating_label)
        )
        counts = {row[0].value if hasattr(row[0], "value") else str(row[0]): int(row[1]) for row in result.all()}
        order = ["EE", "DE", "ME", "SME", "NI"]
        return [{"name": label, "value": counts.get(label, 0)} for label in order]

    @staticmethod
    async def _quarterly_trend(user_filter_clause, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(PerformanceReview.cycle_quarter, func.avg(PerformanceReview.overall_rating))
            .where(user_filter_clause)
            .group_by(PerformanceReview.cycle_quarter)
            .order_by(PerformanceReview.cycle_quarter.asc())
        )
        points = [{"name": f"Q{row[0]}", "score": round(float((row[1] or 0) * 20), 1)} for row in result.all()]
        if points:
            return points
        return [{"name": "Q1", "score": 0}, {"name": "Q2", "score": 0}, {"name": "Q3", "score": 0}, {"name": "Q4", "score": 0}]

    @staticmethod
    async def _weekly_velocity(user_id: str, db: AsyncSession) -> list[dict]:
        now = datetime.now(timezone.utc)
        points: list[dict] = []
        for idx in range(4):
            end = now - timedelta(days=7 * (3 - idx))
            start = end - timedelta(days=7)
            result = await db.execute(
                select(
                    func.count(Checkin.id),
                    func.coalesce(
                        func.sum(
                            case((Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1), else_=0)
                        ),
                        0,
                    ),
                )
                .where(
                    and_(
                        Checkin.employee_id == user_id,
                        Checkin.meeting_date >= start,
                        Checkin.meeting_date < end,
                    )
                )
            )
            total, completed = result.one()
            score = (float(completed) / float(total) * 100.0) if total else 0.0
            points.append({"name": f"W{idx + 1}", "score": round(score, 1)})
        return points

    @staticmethod
    async def employee_dashboard(current_user: User, db: AsyncSession) -> dict:
        manager_name = None
        manager_email = None
        manager_title = None
        if current_user.manager_id:
            manager_result = await db.execute(
                select(User.name, User.email, User.title).where(
                    User.id == current_user.manager_id,
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                )
            )
            manager_row = manager_result.one_or_none()
            if manager_row:
                manager_name, manager_email, manager_title = manager_row

        goals_result = await db.execute(
            select(
                func.count(Goal.id),
                func.coalesce(func.sum(case((Goal.progress >= 100, 1), else_=0)), 0),
                func.coalesce(func.avg(Goal.progress), 0),
            ).where(Goal.user_id == current_user.id)
        )
        goals_count, completed_goals, avg_progress = goals_result.one()
        active_goals = max(0, int(goals_count or 0) - int(completed_goals or 0))

        ratings_result = await db.execute(
            select(func.coalesce(func.avg(Rating.rating), 0), func.coalesce(func.max(Rating.created_at), None)).where(
                Rating.employee_id == current_user.id
            )
        )
        avg_rating, latest_rating_time = ratings_result.one()

        latest_rating_result = await db.execute(
            select(Rating.rating)
            .where(Rating.employee_id == current_user.id)
            .order_by(Rating.created_at.desc())
            .limit(1)
        )
        latest_rating = float(latest_rating_result.scalar() or 0)

        checkins_count_result = await db.execute(
            select(func.count(Checkin.id), func.max(Checkin.created_at)).where(Checkin.employee_id == current_user.id)
        )
        checkins_count, last_checkin = checkins_count_result.one()

        now = datetime.now(timezone.utc)
        consistency_series: list[dict] = []
        progress_trend: list[dict] = []
        rating_trend: list[dict] = []

        for idx in range(6):
            end = now - timedelta(days=7 * (5 - idx))
            start = end - timedelta(days=7)
            week_name = f"W{idx + 1}"

            checkin_week_result = await db.execute(
                select(func.count(Checkin.id), func.coalesce(func.avg(Checkin.progress), 0)).where(
                    Checkin.employee_id == current_user.id,
                    Checkin.created_at >= start,
                    Checkin.created_at < end,
                )
            )
            weekly_checkins, weekly_progress = checkin_week_result.one()
            consistency_series.append({"week": week_name, "value": float(weekly_checkins or 0)})
            progress_trend.append({"week": week_name, "value": round(float(weekly_progress or 0), 1)})

            rating_week_result = await db.execute(
                select(func.coalesce(func.avg(Rating.rating), 0)).where(
                    Rating.employee_id == current_user.id,
                    Rating.created_at >= start,
                    Rating.created_at < end,
                )
            )
            weekly_rating = float(rating_week_result.scalar() or 0)
            rating_trend.append({"week": week_name, "value": round(weekly_rating, 2)})

        distribution = await DashboardService._rating_distribution(Rating.employee_id == current_user.id, db)

        consistency_percent = 0.0
        if consistency_series:
            active_weeks = sum(1 for row in consistency_series if row["value"] > 0)
            consistency_percent = round((active_weeks / len(consistency_series)) * 100.0, 1)

        checkin_status = "On Track"
        if not last_checkin:
            checkin_status = "Missed"
        else:
            age_days = (now - last_checkin.astimezone(timezone.utc)).days
            if age_days > 14:
                checkin_status = "Missed"

        readiness_score = (float(avg_progress or 0) * 0.6) + (consistency_percent * 0.4)

        return {
            "progress": round(float(avg_progress or 0), 1),
            "completed_goals": int(completed_goals or 0),
            "active_goals": int(active_goals),
            "avg_rating": round(float(avg_rating or 0), 2),
            "latest_rating": round(float(latest_rating or 0), 2),
            "checkins_count": int(checkins_count or 0),
            "last_checkin": last_checkin,
            "consistency_percent": consistency_percent,
            "manager_name": manager_name,
            "manager_email": manager_email,
            "manager_title": manager_title,
            "review_readiness": DashboardService._bucket_readiness(readiness_score),
            "checkin_status": checkin_status,
            "trend": progress_trend,
            "ratings": rating_trend,
            "distribution": distribution,
            "consistency": consistency_series,
        }

    @staticmethod
    async def employee_overview(current_user: User, db: AsyncSession) -> dict:
        goals_result = await db.execute(select(func.count(Goal.id), func.coalesce(func.avg(Goal.progress), 0)).where(Goal.user_id == current_user.id))
        goals_count, avg_progress = goals_result.one()

        completed_result = await db.execute(select(func.count(Goal.id)).where(Goal.user_id == current_user.id, Goal.progress >= 100))
        goals_completed = int(completed_result.scalar() or 0)

        checkin_result = await db.execute(
            select(
                func.count(Checkin.id),
                func.coalesce(
                    func.sum(
                        case((Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1), else_=0)
                    ),
                    0,
                ),
            )
            .where(Checkin.employee_id == current_user.id)
        )
        total_checkins, completed_checkins = checkin_result.one()
        consistency = (float(completed_checkins) / float(total_checkins) * 100.0) if total_checkins else 0.0

        ratings_count_result = await db.execute(select(func.count(Rating.id)).where(Rating.employee_id == current_user.id))
        peer_signals = int(ratings_count_result.scalar() or 0)

        readiness_score = (float(avg_progress or 0) * 0.65) + (consistency * 0.35)

        trend = await DashboardService._quarterly_trend(PerformanceReview.employee_id == current_user.id, db)
        velocity = await DashboardService._weekly_velocity(str(current_user.id), db)
        distribution = await DashboardService._rating_distribution(Rating.employee_id == current_user.id, db)

        return {
            "role": "employee",
            "kpi": {
                "goals_completed": goals_completed,
                "consistency": round(consistency, 1),
                "review_readiness": DashboardService._bucket_readiness(readiness_score),
                "peer_signals": peer_signals,
            },
            "trend": trend,
            "velocity": velocity,
            "distribution": distribution,
            "heatmap": [float(avg_progress or 0)],
            "stack_ranking": [],
            "insights": {
                "primary": f"Average goal progress is {round(float(avg_progress or 0), 1)}% across {int(goals_count or 0)} goals.",
                "secondary": f"Check-in completion consistency is {round(consistency, 1)}%.",
            },
        }

    @staticmethod
    async def manager_overview(current_user: User, db: AsyncSession) -> dict:
        team_result = await db.execute(select(User).where(User.manager_id == current_user.id, User.is_active.is_(True)).order_by(User.name.asc()))
        team_members = list(team_result.scalars().all())
        team_ids = [member.id for member in team_members]

        if not team_ids:
            return {
                "role": "manager",
                "kpi": {"team_goals": 0, "consistency": 0, "at_risk_goals": 0, "active_reports": 0},
                "trend": [{"name": "Q1", "score": 0}, {"name": "Q2", "score": 0}, {"name": "Q3", "score": 0}, {"name": "Q4", "score": 0}],
                "velocity": [{"name": "W1", "score": 0}, {"name": "W2", "score": 0}, {"name": "W3", "score": 0}, {"name": "W4", "score": 0}],
                "distribution": [{"name": "EE", "value": 0}, {"name": "DE", "value": 0}, {"name": "ME", "value": 0}, {"name": "SME", "value": 0}, {"name": "NI", "value": 0}],
                "heatmap": [],
                "stack_ranking": [],
                "insights": {
                    "primary": "No direct reports assigned yet.",
                    "secondary": "Assign reportees to see team analytics.",
                },
            }

        goals_result = await db.execute(
            select(func.count(Goal.id), func.coalesce(func.avg(Goal.progress), 0), func.coalesce(func.sum(case((Goal.progress < 40, 1), else_=0)), 0))
            .where(Goal.user_id.in_(team_ids))
        )
        team_goals, avg_progress, at_risk_goals = goals_result.one()

        checkin_result = await db.execute(
            select(
                func.count(Checkin.id),
                func.coalesce(
                    func.sum(
                        case((Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1), else_=0)
                    ),
                    0,
                ),
            )
            .where(Checkin.employee_id.in_(team_ids))
        )
        total_checkins, completed_checkins = checkin_result.one()
        consistency = (float(completed_checkins) / float(total_checkins) * 100.0) if total_checkins else 0.0

        heatmap: list[float] = []
        stack_ranking: list[dict] = []
        for member in team_members:
            member_goal = await db.execute(select(func.coalesce(func.avg(Goal.progress), 0)).where(Goal.user_id == member.id))
            progress = float(member_goal.scalar() or 0)
            heatmap.append(round(progress, 1))

            member_rating = await db.execute(select(func.coalesce(func.avg(Rating.rating), 0)).where(Rating.employee_id == member.id))
            score = float(member_rating.scalar() or 0) * 20
            trend = "up" if score >= 80 else "flat" if score >= 60 else "down"
            stack_ranking.append({"name": member.name, "score": round(score, 1), "trend": trend})

        stack_ranking.sort(key=lambda row: row["score"], reverse=True)

        trend = await DashboardService._quarterly_trend(PerformanceReview.manager_id == current_user.id, db)
        distribution = await DashboardService._rating_distribution(Rating.employee_id.in_(team_ids), db)

        return {
            "role": "manager",
            "kpi": {
                "team_goals": int(team_goals or 0),
                "consistency": round(consistency, 1),
                "at_risk_goals": int(at_risk_goals or 0),
                "active_reports": len(team_members),
            },
            "trend": trend,
            "velocity": [{"name": "W1", "score": round(consistency, 1)}, {"name": "W2", "score": round(consistency, 1)}, {"name": "W3", "score": round(consistency, 1)}, {"name": "W4", "score": round(consistency, 1)}],
            "distribution": distribution,
            "heatmap": heatmap,
            "stack_ranking": stack_ranking[:10],
            "insights": {
                "primary": f"Team average goal progress is {round(float(avg_progress or 0), 1)}%.",
                "secondary": f"At-risk goal count is {int(at_risk_goals or 0)}.",
            },
        }

    @staticmethod
    async def org_overview(current_user: User, db: AsyncSession) -> dict:
        org_users_result = await db.execute(
            select(User.id).where(User.organization_id == current_user.organization_id, User.is_active.is_(True))
        )
        org_user_ids = [row[0] for row in org_users_result.all()]

        if not org_user_ids:
            return {
                "role": "org",
                "kpi": {"org_health": 0, "cycle_completion": 0, "risk_flags": 0, "leadership_signals": 0},
                "trend": [{"name": "Q1", "score": 0}, {"name": "Q2", "score": 0}, {"name": "Q3", "score": 0}, {"name": "Q4", "score": 0}],
                "velocity": [{"name": "W1", "score": 0}, {"name": "W2", "score": 0}, {"name": "W3", "score": 0}, {"name": "W4", "score": 0}],
                "distribution": [{"name": "EE", "value": 0}, {"name": "DE", "value": 0}, {"name": "ME", "value": 0}, {"name": "SME", "value": 0}, {"name": "NI", "value": 0}],
                "heatmap": [],
                "stack_ranking": [],
                "insights": {"primary": "No organization users found.", "secondary": "Data will appear once users are onboarded."},
            }

        goals_result = await db.execute(
            select(func.coalesce(func.avg(Goal.progress), 0), func.coalesce(func.sum(case((Goal.progress < 40, 1), else_=0)), 0), func.count(Goal.id))
            .where(Goal.user_id.in_(org_user_ids))
        )
        avg_progress, risk_flags, total_goals = goals_result.one()

        completed_goals_result = await db.execute(select(func.count(Goal.id)).where(Goal.user_id.in_(org_user_ids), Goal.progress >= 100))
        completed_goals = int(completed_goals_result.scalar() or 0)
        cycle_completion = (float(completed_goals) / float(total_goals) * 100.0) if total_goals else 0.0

        review_result = await db.execute(select(func.count(PerformanceReview.id)).where(PerformanceReview.employee_id.in_(org_user_ids)))
        leadership_signals = int(review_result.scalar() or 0)

        trend = await DashboardService._quarterly_trend(PerformanceReview.employee_id.in_(org_user_ids), db)
        distribution = await DashboardService._rating_distribution(Rating.employee_id.in_(org_user_ids), db)

        return {
            "role": "org",
            "kpi": {
                "org_health": round(float(avg_progress or 0), 1),
                "total_goals": int(total_goals or 0),
                "goals_completed": int(completed_goals or 0),
                "cycle_completion": round(cycle_completion, 1),
                "risk_flags": int(risk_flags or 0),
                "leadership_signals": leadership_signals,
            },
            "trend": trend,
            "velocity": [{"name": "W1", "score": round(float(avg_progress or 0), 1)}, {"name": "W2", "score": round(float(avg_progress or 0), 1)}, {"name": "W3", "score": round(float(avg_progress or 0), 1)}, {"name": "W4", "score": round(float(avg_progress or 0), 1)}],
            "distribution": distribution,
            "heatmap": [round(float(avg_progress or 0), 1)],
            "stack_ranking": [],
            "insights": {
                "primary": f"Organization average goal progress is {round(float(avg_progress or 0), 1)}%.",
                "secondary": f"Cycle completion is {round(cycle_completion, 1)}% with {int(risk_flags or 0)} risk flags.",
            },
        }

    @staticmethod
    async def get_overview(current_user: User, db: AsyncSession, mode: UserRole | None = None) -> dict:
        effective_mode = mode or current_user.role

        if effective_mode == UserRole.employee:
            return await DashboardService.employee_overview(current_user, db)

        if effective_mode == UserRole.manager:
            return await DashboardService.manager_overview(current_user, db)

        return await DashboardService.org_overview(current_user, db)
