from collections import defaultdict
from datetime import datetime, timezone
import json
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import GeminiClient, GeminiClientError
from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.enums import CheckinStatus, UserRole
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.rating import Rating
from app.models.user import User


class HRService:
    @staticmethod
    def _parse_meeting_description(description: str | None) -> tuple[str, str, str | None]:
        if not description:
            return "check-in", "online", None
        try:
            payload = json.loads(description)
            if isinstance(payload, dict):
                meeting_type = str(payload.get("meeting_type") or "check-in")
                mode = str(payload.get("mode") or "online")
                notes = payload.get("notes")
                return meeting_type, mode, str(notes) if notes is not None else None
        except Exception:
            pass
        return "check-in", "online", description

    @staticmethod
    def _status_from_score(score: float) -> str:
        if score >= 75:
            return "On Track"
        if score >= 50:
            return "Needs Attention"
        return "At Risk"

    @staticmethod
    def _needs_training(progress: float, consistency: float, rating: float | None) -> bool:
        return progress < 50 or consistency < 60 or (rating is not None and rating <= 2)

    @staticmethod
    def _training_intensity(progress: float, consistency: float, rating: float | None) -> float:
        intensity = 0.0
        if progress < 50:
            intensity += min(40.0, (50.0 - progress) * 0.8)
        if consistency < 60:
            intensity += min(35.0, (60.0 - consistency) * 0.6)
        if rating is not None and rating <= 2:
            intensity += 25.0
        return round(max(0.0, min(100.0, intensity)), 1)

    @staticmethod
    def _training_score(progress: float, consistency: float, rating: float | None) -> float:
        progress_risk = 0.0 if progress >= 50 else ((50.0 - progress) / 50.0) * 100.0
        consistency_risk = 0.0 if consistency >= 60 else ((60.0 - consistency) / 60.0) * 100.0

        rating_risk = 0.0
        if rating is not None and rating <= 2:
            rating_risk = ((2.0 - rating) / 2.0) * 100.0

        score = (progress_risk * 0.45) + (consistency_risk * 0.35) + (rating_risk * 0.20)
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def _training_level(score: float) -> str:
        if score >= 75:
            return "Critical"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Medium"
        if score >= 15:
            return "Low"
        return "No Need"

    @staticmethod
    async def _employee_metrics(employee_id: UUID, db: AsyncSession) -> dict:
        progress_result = await db.execute(select(func.avg(Goal.progress)).where(Goal.user_id == employee_id))
        progress = float(progress_result.scalar() or 0.0)

        checkin_result = await db.execute(
            select(
                func.count(Checkin.id),
                func.coalesce(
                    func.sum(case((Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]), 1), else_=0)),
                    0,
                ),
            ).where(Checkin.employee_id == employee_id)
        )
        total_checkins, completed_checkins = checkin_result.one()
        consistency = (float(completed_checkins) / float(total_checkins) * 100.0) if total_checkins else 0.0

        rating_result = await db.execute(select(func.avg(Rating.rating)).where(Rating.employee_id == employee_id))
        avg_rating = rating_result.scalar_one_or_none()
        avg_rating_value = float(avg_rating) if avg_rating is not None else None

        if avg_rating_value is not None:
            rating_score = max(0.0, min(100.0, (avg_rating_value / 5.0) * 100.0))
            overall = (progress * 0.45) + (consistency * 0.35) + (rating_score * 0.20)
        else:
            overall = (progress * 0.6) + (consistency * 0.4)

        return {
            "progress": round(progress, 1),
            "consistency": round(consistency, 1),
            "avg_rating": round(avg_rating_value, 2) if avg_rating_value is not None else None,
            "overall": round(overall, 1),
            "status": HRService._status_from_score(overall),
        }

    @staticmethod
    async def _ai_training_reason(employee: User, metrics: dict) -> str:
        rule_result = "YES" if HRService._needs_training(metrics["progress"], metrics["consistency"], metrics["avg_rating"]) else "NO"
        prompt = (
            "Analyze performance and tell if employee needs training. "
            f"Employee: {employee.name}. Department: {employee.department or 'General'}. "
            f"Progress: {metrics['progress']}. Consistency: {metrics['consistency']}. Rating: {metrics['avg_rating']}. "
            "Return concise output as: YES/NO then one-line reason."
        )
        try:
            client = GeminiClient()
            result = await client.generate(prompt)
            text = (result.text or "").strip()
            if text:
                return text
        except (GeminiClientError, Exception):
            pass
        return f"{rule_result} - Rule-based analysis on progress/consistency/rating thresholds."

    @staticmethod
    async def list_managers(current_user: User, db: AsyncSession, department: str | None = None) -> list[User]:
        stmt = select(User).where(
            User.organization_id == current_user.organization_id,
            User.role == UserRole.manager,
            User.is_active.is_(True),
        )
        if department:
            stmt = stmt.where(User.department == department)
        result = await db.execute(stmt.order_by(User.name.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_overview(current_user: User, db: AsyncSession) -> dict:
        employees_result = await db.execute(
            select(User)
            .where(
                User.organization_id == current_user.organization_id,
                User.role == UserRole.employee,
                User.is_active.is_(True),
            )
            .order_by(User.department.asc(), User.name.asc())
        )
        employees = list(employees_result.scalars().all())

        managers_result = await db.execute(
            select(func.count(User.id)).where(
                User.organization_id == current_user.organization_id,
                User.role == UserRole.manager,
                User.is_active.is_(True),
            )
        )
        total_managers = int(managers_result.scalar() or 0)

        heatmap = []
        overall_scores = []
        at_risk = 0
        for employee in employees:
            metrics = await HRService._employee_metrics(employee.id, db)
            overall_scores.append(metrics["overall"])
            if metrics["status"] == "At Risk":
                at_risk += 1
            needs_training = HRService._needs_training(metrics["progress"], metrics["consistency"], metrics["avg_rating"])
            score = HRService._training_score(metrics["progress"], metrics["consistency"], metrics["avg_rating"])
            heatmap.append(
                {
                    "employee_id": str(employee.id),
                    "employee_name": employee.name,
                    "progress": metrics["progress"],
                    "consistency": metrics["consistency"],
                    "rating": metrics["avg_rating"],
                    "intensity": score,
                    "training_need_level": HRService._training_level(score),
                    "needs_training": needs_training,
                }
            )

        return {
            "total_employees": len(employees),
            "total_managers": total_managers,
            "at_risk_employees": at_risk,
            "avg_org_performance": round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0.0,
            "training_heatmap": heatmap,
        }

    @staticmethod
    async def list_employee_directory(
        current_user: User,
        db: AsyncSession,
        department: str | None = None,
        manager_id: str | None = None,
        needs_training: bool | None = None,
    ) -> list[dict]:
        stmt = select(User).where(
            User.organization_id == current_user.organization_id,
            User.role == UserRole.employee,
            User.is_active.is_(True),
        )
        if department:
            stmt = stmt.where(User.department == department)
        if manager_id:
            try:
                stmt = stmt.where(User.manager_id == UUID(manager_id))
            except ValueError:
                return []

        result = await db.execute(stmt.order_by(User.name.asc()))
        employees = list(result.scalars().all())
        manager_map: dict[UUID, tuple[str, str | None]] = {}

        rows = []
        for employee in employees:
            if employee.manager_id and employee.manager_id not in manager_map:
                manager = await db.get(User, employee.manager_id)
                manager_map[employee.manager_id] = (manager.name if manager else "", manager.email if manager else None)
            metrics = await HRService._employee_metrics(employee.id, db)
            training_flag = HRService._needs_training(metrics["progress"], metrics["consistency"], metrics["avg_rating"])
            if needs_training is not None and training_flag != needs_training:
                continue
            manager_name = manager_map.get(employee.manager_id, (None, None))[0] if employee.manager_id else None
            manager_email = manager_map.get(employee.manager_id, (None, None))[1] if employee.manager_id else None
            rows.append(
                {
                    "id": str(employee.id),
                    "name": employee.name,
                    "email": employee.email,
                    "role": employee.title or employee.role.value,
                    "department": employee.department or "General",
                    "manager_name": manager_name,
                    "manager_email": manager_email,
                    "progress": metrics["progress"],
                    "rating": metrics["avg_rating"],
                    "consistency": metrics["consistency"],
                    "needs_training": training_flag,
                }
            )
        return rows

    @staticmethod
    async def get_employee_profile(current_user: User, employee_id: str, db: AsyncSession) -> dict | None:
        try:
            employee_uuid = UUID(employee_id)
        except ValueError:
            return None

        employee = await db.get(User, employee_uuid)
        if not employee or employee.organization_id != current_user.organization_id:
            return None

        manager_name = None
        if employee.manager_id:
            manager = await db.get(User, employee.manager_id)
            manager_name = manager.name if manager else None

        goals_result = await db.execute(select(Goal).where(Goal.user_id == employee.id).order_by(Goal.updated_at.desc()))
        goals = list(goals_result.scalars().all())

        checkins_result = await db.execute(
            select(Checkin).where(Checkin.employee_id == employee.id).order_by(Checkin.created_at.desc())
        )
        checkins = list(checkins_result.scalars().all())

        ratings_result = await db.execute(
            select(Rating).where(Rating.employee_id == employee.id).order_by(Rating.created_at.desc())
        )
        ratings = list(ratings_result.scalars().all())

        metrics = await HRService._employee_metrics(employee.id, db)
        reason = await HRService._ai_training_reason(employee, metrics)

        trend_by_week: dict[str, list[float]] = defaultdict(list)
        for checkin in checkins:
            key = checkin.created_at.strftime("%Y-W%W")
            trend_by_week[key].append(float(checkin.progress))

        performance_trend = [
            {"week": week, "progress": round(sum(values) / len(values), 1)}
            for week, values in sorted(trend_by_week.items())
        ]

        return {
            "id": str(employee.id),
            "name": employee.name,
            "role": employee.title or employee.role.value,
            "department": employee.department or "General",
            "manager_name": manager_name,
            "progress": metrics["progress"],
            "consistency": metrics["consistency"],
            "avg_rating": metrics["avg_rating"] or 0.0,
            "needs_training": HRService._needs_training(metrics["progress"], metrics["consistency"], metrics["avg_rating"]),
            "ai_training_reason": reason,
            "goals": [
                {"id": str(goal.id), "title": goal.title, "progress": float(goal.progress), "status": goal.status.value}
                for goal in goals
            ],
            "checkins": [
                {
                    "id": str(item.id),
                    "progress": int(item.progress),
                    "status": item.status.value,
                    "summary": item.summary,
                    "manager_feedback": item.manager_feedback,
                    "created_at": item.created_at.isoformat(),
                }
                for item in checkins
            ],
            "ratings": [
                {
                    "id": str(item.id),
                    "rating": int(item.rating),
                    "rating_label": item.rating_label.value,
                    "comments": item.comments,
                    "created_at": item.created_at.isoformat(),
                }
                for item in ratings
            ],
            "performance_trend": performance_trend,
        }

    @staticmethod
    async def get_manager_team_analytics(current_user: User, manager_id: str, db: AsyncSession) -> dict | None:
        try:
            manager_uuid = UUID(manager_id)
        except ValueError:
            return None

        manager = await db.get(User, manager_uuid)
        if not manager or manager.organization_id != current_user.organization_id or manager.role != UserRole.manager:
            return None

        members = await HRService.get_team_performance(current_user=current_user, manager_id=manager_id, db=db)
        if not members:
            return {
                "manager_id": str(manager.id),
                "manager_name": manager.name,
                "team_size": 0,
                "avg_performance": 0.0,
                "consistency": 0.0,
                "at_risk_employees": 0,
                "top_performers": [],
                "low_performers": [],
                "workload_distribution": [],
                "rating_distribution": [],
                "members": [],
            }

        scored = []
        workload = []
        rating_distribution_count: dict[str, int] = defaultdict(int)
        for member in members:
            score = (member["progress"] * 0.6) + (member["consistency"] * 0.4)
            scored.append({"employee": member["name"], "score": round(score, 1)})
            member_uuid = UUID(member["id"])
            weight_result = await db.execute(select(func.coalesce(func.sum(Goal.weightage), 0)).where(Goal.user_id == member_uuid))
            workload.append({"employee": member["name"], "weightage": float(weight_result.scalar() or 0.0)})
            if member["rating"] is not None:
                rating_distribution_count[str(member["rating"])] += 1

        scored_sorted = sorted(scored, key=lambda item: item["score"], reverse=True)
        at_risk = sum(1 for member in members if member["status"] == "At Risk")
        avg_perf = round(sum(item["score"] for item in scored) / len(scored), 1)
        avg_consistency = round(sum(member["consistency"] for member in members) / len(members), 1)

        return {
            "manager_id": str(manager.id),
            "manager_name": manager.name,
            "team_size": len(members),
            "avg_performance": avg_perf,
            "consistency": avg_consistency,
            "at_risk_employees": at_risk,
            "top_performers": scored_sorted[:3],
            "low_performers": list(reversed(scored_sorted[-3:])),
            "workload_distribution": workload,
            "rating_distribution": [{"label": k, "count": v} for k, v in sorted(rating_distribution_count.items())],
            "members": members,
        }

    @staticmethod
    async def get_org_analytics(current_user: User, db: AsyncSession) -> dict:
        goal_week_bucket = func.date_trunc("week", Goal.updated_at).label("goal_week_bucket")
        checkin_week_bucket = func.date_trunc("week", Checkin.created_at).label("checkin_week_bucket")

        performance_rows = await db.execute(
            select(goal_week_bucket, func.avg(Goal.progress))
            .join(User, Goal.user_id == User.id)
            .where(User.organization_id == current_user.organization_id)
            .group_by(goal_week_bucket)
            .order_by(goal_week_bucket)
        )

        dept_rows = await db.execute(
            select(User.department, func.avg(Goal.progress))
            .join(Goal, Goal.user_id == User.id)
            .where(User.organization_id == current_user.organization_id)
            .group_by(User.department)
            .order_by(User.department.asc())
        )

        rating_rows = await db.execute(
            select(Rating.rating_label, func.count(Rating.id))
            .join(User, Rating.employee_id == User.id)
            .where(User.organization_id == current_user.organization_id)
            .group_by(Rating.rating_label)
        )

        consistency_rows = await db.execute(
            select(checkin_week_bucket, func.avg(Checkin.progress))
            .join(User, Checkin.employee_id == User.id)
            .where(User.organization_id == current_user.organization_id)
            .group_by(checkin_week_bucket)
            .order_by(checkin_week_bucket)
        )

        return {
            "performance_trend": [
                {"week": row[0].strftime("%Y-%m-%d"), "value": round(float(row[1] or 0), 1)}
                for row in performance_rows.all()
            ],
            "department_comparison": [
                {"department": row[0] or "General", "value": round(float(row[1] or 0), 1)}
                for row in dept_rows.all()
            ],
            "rating_distribution": [
                {"label": row[0].value if row[0] else "N/A", "count": int(row[1] or 0)}
                for row in rating_rows.all()
            ],
            "checkin_consistency": [
                {"week": row[0].strftime("%Y-%m-%d"), "value": round(float(row[1] or 0), 1)}
                for row in consistency_rows.all()
            ],
        }

    @staticmethod
    async def get_calibration(current_user: User, db: AsyncSession) -> dict:
        rows = await db.execute(
            select(User.id, User.name, func.avg(Rating.rating))
            .join(Rating, Rating.manager_id == User.id)
            .where(User.organization_id == current_user.organization_id, User.role == UserRole.manager)
            .group_by(User.id, User.name)
        )
        manager_rows = list(rows.all())
        org_avg = round(
            sum(float(row[2] or 0.0) for row in manager_rows) / len(manager_rows),
            2,
        ) if manager_rows else 0.0

        managers = []
        for manager_id, manager_name, avg_rating in manager_rows:
            avg_value = round(float(avg_rating or 0.0), 2)
            delta = round(avg_value - org_avg, 2)
            if delta > 0.35:
                direction = "Higher than org average"
            elif delta < -0.35:
                direction = "Lower than org average"
            else:
                direction = "Aligned with org average"
            managers.append(
                {
                    "manager_id": str(manager_id),
                    "manager_name": manager_name,
                    "avg_rating": avg_value,
                    "org_avg_rating": org_avg,
                    "bias_direction": direction,
                    "delta": delta,
                }
            )

        return {"managers": managers}

    @staticmethod
    async def generate_report(current_user: User, report_type: str, db: AsyncSession) -> dict:
        report_key = report_type.strip().lower()
        if report_key == "employee":
            rows = await HRService.list_employee_directory(current_user=current_user, db=db)
        elif report_key == "team":
            managers = await HRService.list_managers(current_user=current_user, db=db)
            rows = []
            for manager in managers:
                payload = await HRService.get_manager_team_analytics(current_user=current_user, manager_id=str(manager.id), db=db)
                if payload:
                    rows.append(payload)
        else:
            rows = [await HRService.get_org_analytics(current_user=current_user, db=db)]

        return {
            "report_type": report_key,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        }

    @staticmethod
    async def list_meetings(
        current_user: User,
        db: AsyncSession,
        employee_id: str | None = None,
        manager_id: str | None = None,
    ) -> list[dict]:
        stmt = (
            select(Meeting)
            .join(User, Meeting.organizer_id == User.id)
            .where(User.organization_id == current_user.organization_id)
            .order_by(Meeting.start_time.desc())
        )

        if employee_id:
            try:
                stmt = stmt.where(Meeting.employee_id == UUID(employee_id))
            except ValueError:
                return []
        if manager_id:
            try:
                stmt = stmt.where(Meeting.manager_id == UUID(manager_id))
            except ValueError:
                return []

        result = await db.execute(stmt)
        meetings = list(result.scalars().all())

        organizer_ids = list({meeting.organizer_id for meeting in meetings if meeting.organizer_id})
        organizer_role_map: dict[UUID, str] = {}
        if organizer_ids:
            organizer_result = await db.execute(select(User.id, User.role).where(User.id.in_(organizer_ids)))
            organizer_role_map = {row[0]: row[1].value for row in organizer_result.all()}

        checkin_ids = [meeting.checkin_id for meeting in meetings if meeting.checkin_id]
        rated_checkin_ids: set[UUID] = set()
        if checkin_ids:
            ratings_result = await db.execute(
                select(CheckinRating.checkin_id)
                .where(CheckinRating.checkin_id.in_(checkin_ids))
                .group_by(CheckinRating.checkin_id)
            )
            rated_checkin_ids = {row[0] for row in ratings_result.all() if row[0] is not None}

        names_cache: dict[UUID, str] = {}
        rows = []
        for meeting in meetings:
            _, mode, notes = HRService._parse_meeting_description(meeting.description)
            employee_name = None
            manager_name = None
            if meeting.employee_id:
                if meeting.employee_id not in names_cache:
                    employee = await db.get(User, meeting.employee_id)
                    names_cache[meeting.employee_id] = employee.name if employee else ""
                employee_name = names_cache.get(meeting.employee_id) or None
            if meeting.manager_id:
                if meeting.manager_id not in names_cache:
                    manager = await db.get(User, meeting.manager_id)
                    names_cache[meeting.manager_id] = manager.name if manager else ""
                manager_name = names_cache.get(meeting.manager_id) or None

            rows.append(
                {
                    "id": str(meeting.id),
                    "title": meeting.title,
                    "description": notes if notes else None,
                    "employee_id": str(meeting.employee_id) if meeting.employee_id else None,
                    "employee_name": employee_name,
                    "manager_id": str(meeting.manager_id) if meeting.manager_id else None,
                    "manager_name": manager_name,
                    "start_time": meeting.start_time.isoformat(),
                    "end_time": meeting.end_time.isoformat(),
                    "duration_minutes": max(1, int((meeting.end_time - meeting.start_time).total_seconds() // 60)),
                    "meeting_type": meeting.meeting_type.value,
                    "mode": mode,
                    "notes": notes,
                    "participants": list(meeting.participants or []),
                    "meet_link": meeting.meet_link or meeting.google_meet_link,
                    "google_event_id": meeting.google_event_id,
                    "summary": meeting.summary,
                    "status": meeting.status.value,
                    "created_by_role": organizer_role_map.get(meeting.organizer_id, "manager"),
                    "created_from_checkin": meeting.checkin_id is not None,
                    "rating_given": bool(meeting.checkin_id and meeting.checkin_id in rated_checkin_ids),
                }
            )
        return rows

    @staticmethod
    async def summarize_meeting(current_user: User, meeting_id: str, transcript: str, db: AsyncSession) -> dict | None:
        try:
            meeting_uuid = UUID(meeting_id)
        except ValueError:
            return None

        meeting = await db.get(Meeting, meeting_uuid)
        if not meeting:
            return None

        owner_result = await db.execute(
            select(User.organization_id).where(User.id == meeting.organizer_id)
        )
        organization_id = owner_result.scalar_one_or_none()
        if organization_id != current_user.organization_id:
            return None

        prompt = (
            "Summarize this meeting discussion and highlight key points.\n"
            f"Transcript:\n{transcript}\n"
            "Return concise plain text summary with bullet-like sentences."
        )

        summary = "Summary unavailable"
        try:
            client = GeminiClient()
            result = await client.generate(prompt)
            if (result.text or "").strip():
                summary = result.text.strip()
        except (GeminiClientError, Exception):
            summary = "Summary unavailable. AI service is not configured or currently unavailable."

        meeting.summary = summary
        await db.commit()

        return {"meeting_id": str(meeting.id), "summary": summary}

    @staticmethod
    async def _build_employee_performance_row(member: User, db: AsyncSession) -> dict:
        metrics = await HRService._employee_metrics(member.id, db)
        progress = metrics["progress"]
        consistency = metrics["consistency"]

        last_checkin_result = await db.execute(
            select(Checkin.status)
            .where(Checkin.employee_id == member.id)
            .order_by(Checkin.meeting_date.desc())
            .limit(1)
        )
        last_checkin_status = last_checkin_result.scalar_one_or_none()
        last_checkin_label = last_checkin_status.value if last_checkin_status else "none"

        latest_rating = metrics["avg_rating"]
        status = metrics["status"]

        return {
            "id": str(member.id),
            "name": member.name,
            "role": member.title or member.role.value,
            "department": member.department or "General",
            "progress": round(progress, 1),
            "consistency": round(consistency, 1),
            "last_checkin_status": last_checkin_label,
            "rating": int(round(latest_rating)) if latest_rating is not None else None,
            "status": status,
        }

    @staticmethod
    async def get_team_performance(
        current_user: User,
        manager_id: str,
        db: AsyncSession,
        department: str | None = None,
        role: str | None = None,
        performance: str | None = None,
    ) -> list[dict]:
        try:
            manager_uuid = UUID(manager_id)
        except ValueError:
            return []

        manager = await db.get(User, manager_uuid)
        if not manager or manager.organization_id != current_user.organization_id or manager.role != UserRole.manager:
            return []

        stmt = select(User).where(
            User.organization_id == current_user.organization_id,
            User.manager_id == manager.id,
            User.is_active.is_(True),
        )
        if department:
            stmt = stmt.where(User.department == department)
        if role:
            stmt = stmt.where(User.title == role)

        team_result = await db.execute(stmt.order_by(User.name.asc()))
        team_members = list(team_result.scalars().all())

        rows: list[dict] = []
        for member in team_members:
            rows.append(await HRService._build_employee_performance_row(member, db))

        if performance:
            normalized = performance.strip().lower()
            rows = [
                row
                for row in rows
                if row["status"].lower().replace(" ", "_") == normalized
            ]

        return rows

    @staticmethod
    def build_team_insights(team_rows: list[dict]) -> list[str]:
        if not team_rows:
            return ["No team members found for the selected manager and filters."]

        at_risk = sum(1 for member in team_rows if member["status"] == "At Risk")
        needs_attention = sum(1 for member in team_rows if member["status"] == "Needs Attention")
        on_track = sum(1 for member in team_rows if member["status"] == "On Track")

        avg_progress = round(sum(member["progress"] for member in team_rows) / len(team_rows), 1)
        avg_consistency = round(sum(member["consistency"] for member in team_rows) / len(team_rows), 1)

        return [
            f"{at_risk} employees are at risk.",
            f"{needs_attention} employees need attention and {on_track} are on track.",
            f"Average goal completion is {avg_progress}% with consistency at {avg_consistency}%.",
        ]
