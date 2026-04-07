from datetime import datetime, timedelta, timezone
import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.google.calendar_client import GoogleCalendarAPIError, GoogleCalendarAuthError
from app.integrations.google.calendar_service import CalendarService
from app.ai.ai_service import AIService
from app.integrations.google.token_service import GoogleTokenRefreshError, GoogleTokenService
from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.meeting_proposal import MeetingProposal
from app.models.performance_cycle import PerformanceCycle
from app.models.enums import CheckinStatus, GoalStatus, MeetingProposalStatus, MeetingStatus, UserRole
from app.models.user import User
from app.services.cycle_guard import ensure_cycle_writable
from app.schemas.checkin import CheckinRateRequest, CheckinReviewUpdate, CheckinSubmit, CheckinTranscriptIngestRequest


class CheckinService:
    logger = logging.getLogger(__name__)

    @staticmethod
    def _next_working_day_start(now_utc: datetime) -> datetime:
        cursor = now_utc.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        while cursor.weekday() >= 5:
            cursor += timedelta(days=1)
        return cursor

    @staticmethod
    async def _find_best_slot(employee: User, manager: User) -> tuple[datetime, datetime]:
        now_utc = datetime.now(timezone.utc)
        window_start = CheckinService._next_working_day_start(now_utc)

        cursor = window_start
        working_days = 0
        while working_days < 3:
            if cursor.weekday() < 5:
                working_days += 1
            cursor += timedelta(days=1)
        window_end = (cursor - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

        if manager.google_refresh_token and employee.email and manager.email:
            try:
                access_token, _ = await GoogleTokenService.get_google_access_token(manager.google_refresh_token)
                calendar_service = CalendarService(access_token)
                slots = await calendar_service.get_available_slots(
                    participants_emails=[employee.email, manager.email],
                    start_time=window_start,
                    end_time=window_end,
                    slot_minutes=30,
                )
                if slots:
                    start_slot = datetime.fromisoformat(slots[0]["start"])
                    end_slot = datetime.fromisoformat(slots[0]["end"])
                    return start_slot, end_slot
            except (GoogleTokenRefreshError, GoogleCalendarAuthError, GoogleCalendarAPIError):
                pass

        fallback_start = window_start.replace(hour=10, minute=0)
        fallback_end = fallback_start + timedelta(minutes=30)
        return fallback_start, fallback_end

    @staticmethod
    def _generate_insights(*, previous_progress: float, current_progress: int, blockers: str | None) -> list[str]:
        insights: list[str] = []
        if current_progress > previous_progress:
            insights.append("Employee is improving")
        elif current_progress < previous_progress:
            insights.append("Employee is falling behind")

        if blockers and blockers.strip():
            insights.append("Blockers detected")

        if not insights:
            insights.append("Progress is steady")

        return insights

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().lower().split())

    @staticmethod
    def _goal_summary_for_item(goal: Goal, key_points: list[str], action_items: list[str]) -> str:
        title_tokens = [token for token in CheckinService._normalize_text(goal.title).split(" ") if len(token) >= 4]

        matched_lines: list[str] = []
        for row in key_points + action_items:
            line = row.strip()
            if not line:
                continue
            lowered = CheckinService._normalize_text(line)
            if any(token in lowered for token in title_tokens):
                matched_lines.append(line)

        if not matched_lines:
            if action_items:
                return action_items[0]
            if key_points:
                return key_points[0]
            return "No goal-specific summary extracted"

        return "; ".join(matched_lines[:2])

    @staticmethod
    async def _active_cycle_for_employee(current_user: User, db: AsyncSession) -> PerformanceCycle:
        cycle_result = await db.execute(
            select(PerformanceCycle)
            .where(
                PerformanceCycle.organization_id == current_user.organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .order_by(PerformanceCycle.start_date.desc())
            .limit(1)
        )
        cycle = cycle_result.scalar_one_or_none()
        if not cycle:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active cycle found for this employee")
        return cycle

    @staticmethod
    async def submit_checkin(current_user: User, payload: CheckinSubmit, db: AsyncSession) -> tuple[Checkin, list[str]]:
        if current_user.role != UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can submit check-ins")

        cycle = await CheckinService._active_cycle_for_employee(current_user, db)
        await ensure_cycle_writable(db, cycle.id, locked_detail="Cannot submit check-in for a locked cycle")

        if not current_user.manager_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee has no reporting manager")

        manager = await db.get(User, current_user.manager_id)
        if not manager:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reporting manager not found")

        goals_result = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == current_user.id,
                Goal.cycle_id == cycle.id,
                Goal.status == GoalStatus.approved,
            )
            .order_by(Goal.created_at.asc())
        )
        goals = list(goals_result.scalars().all())
        if not goals:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-ins are blocked until goals are approved")

        now = datetime.now(timezone.utc)
        quarter = ((now.month - 1) // 3) + 1
        year = now.year

        quarter_count_result = await db.execute(
            select(func.count(Checkin.id)).where(
                Checkin.employee_id == current_user.id,
                Checkin.cycle_id == cycle.id,
                Checkin.quarter == quarter,
                Checkin.year == year,
            )
        )
        quarter_count = int(quarter_count_result.scalar() or 0)
        cap = max(int(cycle.checkin_cap_per_quarter or 5), 1)
        if quarter_count >= cap:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Quarterly check-in cap reached ({cap})")

        update_map = {str(item.goal_id): item for item in payload.goal_updates}
        for goal in goals:
            goal_update = update_map.get(str(goal.id))
            if goal_update and goal_update.progress is not None:
                goal.progress = goal_update.progress

        previous_progress = round(sum(float(goal.progress or 0.0) for goal in goals) / len(goals), 1) if goals else 0.0
        goal_ids = [goal.id for goal in goals]
        goal_updates = [
            {
                "goal_id": str(goal.id),
                "progress": int(goal.progress or 0),
                "note": (update_map.get(str(goal.id)).note if update_map.get(str(goal.id)) else None),
            }
            for goal in goals
        ]

        proposed_start, proposed_end = await CheckinService._find_best_slot(current_user, manager)
        checkin = Checkin(
            cycle_id=cycle.id,
            goal_ids=goal_ids,
            goal_updates=goal_updates,
            employee_id=current_user.id,
            manager_id=current_user.manager_id,
            overall_progress=payload.overall_progress,
            status=CheckinStatus.submitted,
            meeting_date=proposed_start,
            summary=payload.summary,
            achievements=payload.achievements,
            blockers=payload.blockers,
            confidence_level=payload.confidence_level,
            is_final=bool(getattr(payload, "is_final", False)),
            quarter=quarter,
            year=year,
        )
        db.add(checkin)
        await db.flush()

        proposal = MeetingProposal(
            checkin_id=checkin.id,
            employee_id=current_user.id,
            manager_id=current_user.manager_id,
            proposed_start_time=proposed_start,
            proposed_end_time=proposed_end,
        )
        db.add(proposal)
        await db.commit()
        await db.refresh(checkin)

        CheckinService.logger.info(
            "Check-in submitted",
            extra={
                "checkin_id": str(checkin.id),
                "goal_count": len(goal_ids),
                "employee_id": str(checkin.employee_id),
                "cycle_id": str(checkin.cycle_id) if checkin.cycle_id else None,
            },
        )

        insights = CheckinService._generate_insights(
            previous_progress=previous_progress,
            current_progress=payload.overall_progress,
            blockers=payload.blockers,
        )
        return checkin, insights

    @staticmethod
    async def list_pending_meeting_proposals(current_user: User, db: AsyncSession) -> list[MeetingProposal]:
        stmt = (
            select(MeetingProposal)
            .where(
                MeetingProposal.manager_id == current_user.id,
                MeetingProposal.status == MeetingProposalStatus.pending,
            )
            .order_by(MeetingProposal.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_employee_checkins(current_user: User, db: AsyncSession) -> list[Checkin]:
        stmt = (
            select(Checkin)
            .where(Checkin.employee_id == current_user.id)
            .order_by(Checkin.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_pending_for_manager(current_user: User, db: AsyncSession) -> list[dict]:
        stmt = (
            select(
                Checkin.id,
                Checkin.employee_id,
                User.name,
                Checkin.goal_ids,
                Checkin.overall_progress,
                Checkin.summary,
                Checkin.achievements,
                Checkin.blockers,
                Checkin.status,
                Checkin.created_at,
            )
            .join(User, User.id == Checkin.employee_id)
            .where(
                Checkin.manager_id == current_user.id,
                Checkin.status == CheckinStatus.submitted,
            )
            .order_by(Checkin.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        all_goal_ids: set[str] = set()
        for row in rows:
            for goal_id in row[3] or []:
                all_goal_ids.add(str(goal_id))

        goal_title_map: dict[str, str] = {}
        if all_goal_ids:
            goals_result = await db.execute(select(Goal.id, Goal.title).where(Goal.id.in_(list(all_goal_ids))))
            goal_title_map = {str(goal_id): title for goal_id, title in goals_result.all()}

        return [
            {
                "id": row[0],
                "employee_id": row[1],
                "employee_name": row[2],
                "goal_ids": row[3] or [],
                "goal_titles": [goal_title_map.get(str(goal_id), str(goal_id)) for goal_id in (row[3] or [])],
                "overall_progress": row[4],
                "summary": row[5],
                "achievements": row[6],
                "blockers": row[7],
                "status": row[8],
                "created_at": row[9],
            }
            for row in rows
        ]

    @staticmethod
    async def review_checkin(checkin_id: str, payload: CheckinReviewUpdate, current_user: User, db: AsyncSession) -> Checkin:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can review check-ins")

        checkin = await db.get(Checkin, checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        if checkin.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your direct report check-in")
        await ensure_cycle_writable(db, checkin.cycle_id, locked_detail="Cannot review check-in in a locked cycle")

        if payload.status not in {CheckinStatus.reviewed, CheckinStatus.draft}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager can set status to reviewed or draft")

        checkin.manager_feedback = payload.manager_feedback
        checkin.status = payload.status
        await db.commit()
        await db.refresh(checkin)
        return checkin

    @staticmethod
    async def rate_checkin(
        checkin_id: str,
        payload: CheckinRateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> CheckinRating:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can rate check-ins")

        checkin = await db.get(Checkin, checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        if checkin.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your direct report check-in")
        await ensure_cycle_writable(db, checkin.cycle_id, locked_detail="Cannot rate check-in in a locked cycle")

        meeting_result = await db.execute(
            select(Meeting)
            .where(Meeting.checkin_id == checkin.id)
            .order_by(Meeting.start_time.desc())
            .limit(1)
        )
        meeting = meeting_result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in meeting is not scheduled")

        now_utc = datetime.now(timezone.utc)
        if meeting.end_time.astimezone(timezone.utc) > now_utc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating is enabled only after meeting end time")

        existing_rating_result = await db.execute(
            select(CheckinRating)
            .where(
                CheckinRating.checkin_id == checkin.id,
                CheckinRating.manager_id == current_user.id,
            )
            .order_by(CheckinRating.created_at.desc())
            .limit(1)
        )
        existing_rating = existing_rating_result.scalar_one_or_none()
        if existing_rating is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post-meeting review already submitted for this check-in")

        rating = CheckinRating(
            cycle_id=checkin.cycle_id,
            checkin_id=checkin.id,
            employee_id=checkin.employee_id,
            manager_id=current_user.id,
            rating=payload.rating,
            feedback=payload.feedback,
        )
        db.add(rating)

        checkin.status = CheckinStatus.reviewed
        if meeting.status != MeetingStatus.completed:
            meeting.status = MeetingStatus.completed

        await db.commit()
        await db.refresh(rating)

        CheckinService.logger.info(
            "Check-in rating submitted",
            extra={
                "checkin_rating_id": str(rating.id),
                "checkin_id": str(rating.checkin_id),
                "employee_id": str(rating.employee_id),
                "manager_id": str(rating.manager_id),
                "cycle_id": str(rating.cycle_id) if rating.cycle_id else None,
            },
        )
        return rating

    @staticmethod
    async def get_employee_final_rating(employee_id: str, current_user: User, db: AsyncSession) -> tuple[float, int]:
        if current_user.role == UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees cannot view ratings")

        if current_user.role == UserRole.manager:
            employee = await db.get(User, employee_id)
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this final rating")

        result = await db.execute(
            select(func.coalesce(func.avg(CheckinRating.rating), 0), func.count(CheckinRating.id)).where(
                CheckinRating.employee_id == employee_id
            )
        )
        avg_value, count_value = result.one()
        return float(avg_value or 0), int(count_value or 0)

    @staticmethod
    async def get_employee_final_ratings_bulk(employee_ids: list[str], current_user: User, db: AsyncSession) -> dict[str, tuple[float, int]]:
        if current_user.role == UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees cannot view ratings")

        unique_employee_ids = list(dict.fromkeys(employee_ids))
        if not unique_employee_ids:
            return {}

        if current_user.role == UserRole.manager:
            employees_result = await db.execute(select(User.id, User.manager_id).where(User.id.in_(unique_employee_ids)))
            allowed_ids = {str(employee_id) for employee_id, manager_id in employees_result.all() if manager_id == current_user.id}
            denied_ids = [employee_id for employee_id in unique_employee_ids if employee_id not in allowed_ids]
            if denied_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view one or more requested final ratings")

        ratings_result = await db.execute(
            select(
                CheckinRating.employee_id,
                func.coalesce(func.avg(CheckinRating.rating), 0),
                func.count(CheckinRating.id),
            )
            .where(CheckinRating.employee_id.in_(unique_employee_ids))
            .group_by(CheckinRating.employee_id)
        )

        grouped = {
            str(employee_id): (float(avg_value or 0), int(count_value or 0))
            for employee_id, avg_value, count_value in ratings_result.all()
        }

        return {employee_id: grouped.get(employee_id, (0.0, 0)) for employee_id in unique_employee_ids}

    @staticmethod
    async def ingest_transcript(
        checkin_id: str,
        payload: CheckinTranscriptIngestRequest,
        current_user: User,
        db: AsyncSession,
    ) -> dict:
        checkin = await db.get(Checkin, checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        if current_user.role == UserRole.employee and checkin.employee_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can ingest transcript only for their own check-ins")
        if current_user.role == UserRole.manager and checkin.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can ingest transcript only for direct-report check-ins")

        ai = AIService()
        summary_payload = await ai.summarize_checkin_transcript(current_user, payload.transcript, db)
        summary = str(summary_payload.get("summary", "")).strip() or "Transcript summary unavailable"
        key_points = [str(item).strip() for item in (summary_payload.get("key_points") or []) if str(item).strip()]
        action_items = [str(item).strip() for item in (summary_payload.get("action_items") or []) if str(item).strip()]

        goals_result = await db.execute(
            select(Goal).where(Goal.id.in_(checkin.goal_ids or []))
        )
        goals = list(goals_result.scalars().all())

        existing_updates = {str(item.get("goal_id")): dict(item) for item in (checkin.goal_updates or []) if isinstance(item, dict)}
        goal_summaries: list[dict] = []
        merged_updates: list[dict] = []

        for goal in goals:
            note = CheckinService._goal_summary_for_item(goal, key_points, action_items)
            current_update = existing_updates.get(str(goal.id), {})
            merged_updates.append(
                {
                    "goal_id": str(goal.id),
                    "progress": current_update.get("progress", int(goal.progress or 0)),
                    "note": note,
                }
            )
            goal_summaries.append(
                {
                    "goal_id": goal.id,
                    "goal_title": goal.title,
                    "summary_note": note,
                }
            )

        checkin.transcript = payload.transcript.strip()
        checkin.summary = summary
        checkin.goal_updates = merged_updates

        await db.commit()
        await db.refresh(checkin)

        return {
            "checkin": checkin,
            "summary": summary,
            "key_points": key_points,
            "action_items": action_items,
            "goal_summaries": goal_summaries,
        }

    @staticmethod
    async def get_rating_recommendation(checkin_id: str, current_user: User, db: AsyncSession) -> dict:
        if current_user.role not in {UserRole.manager, UserRole.hr, UserRole.leadership}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers or HR roles can access rating recommendation")

        checkin = await db.get(Checkin, checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        if current_user.role == UserRole.manager and checkin.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your direct report check-in")

        progress_score = max(min(float(checkin.overall_progress or 0), 100.0), 0.0)
        confidence_value = float(checkin.confidence_level or 3)
        blockers_present = bool((checkin.blockers or "").strip())
        achievements_present = bool((checkin.achievements or "").strip())
        transcript_present = bool((checkin.transcript or "").strip())
        goal_updates_count = len(checkin.goal_updates or [])

        raw = 1.0 + (progress_score / 100.0) * 3.2
        raw += (confidence_value - 3.0) * 0.25
        if achievements_present:
            raw += 0.2
        if blockers_present:
            raw -= 0.5
        if transcript_present:
            raw += 0.15

        suggested_rating = int(round(max(1.0, min(raw, 5.0))))

        confidence = 0.45
        if transcript_present:
            confidence += 0.2
        if goal_updates_count > 0:
            confidence += 0.15
        if checkin.confidence_level is not None:
            confidence += 0.1
        confidence = round(min(confidence, 0.95), 2)

        rationale: list[str] = [
            f"Overall progress is {int(progress_score)}%.",
            f"Employee confidence level is {int(confidence_value)} out of 5.",
        ]
        if blockers_present:
            rationale.append("Open blockers reduce recommendation certainty and rating headroom.")
        else:
            rationale.append("No blockers were reported in this check-in.")
        if transcript_present:
            rationale.append("Transcript context is available and was included for recommendation quality.")
        else:
            rationale.append("Transcript context is missing, so recommendation confidence is lower.")

        factors = {
            "overall_progress": int(progress_score),
            "confidence_level": int(confidence_value),
            "blockers_present": blockers_present,
            "achievements_present": achievements_present,
            "transcript_present": transcript_present,
            "goal_updates_count": goal_updates_count,
        }

        return {
            "checkin_id": checkin.id,
            "suggested_rating": suggested_rating,
            "confidence": confidence,
            "rationale": rationale,
            "factors": factors,
            "override_allowed": True,
        }
