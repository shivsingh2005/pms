from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.google.calendar_client import GoogleCalendarAPIError, GoogleCalendarAuthError
from app.integrations.google.calendar_service import CalendarService
from app.integrations.google.token_service import GoogleTokenRefreshError, GoogleTokenService
from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.meeting_proposal import MeetingProposal
from app.models.enums import CheckinStatus, MeetingProposalStatus, MeetingStatus, UserRole
from app.models.user import User
from app.schemas.checkin import CheckinRateRequest, CheckinReviewUpdate, CheckinSubmit


class CheckinService:
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
    async def submit_checkin(current_user: User, payload: CheckinSubmit, db: AsyncSession) -> tuple[Checkin, list[str]]:
        if current_user.role != UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can submit check-ins")

        goal = await db.get(Goal, payload.goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        if goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Goal does not belong to current employee")

        if not current_user.manager_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee has no reporting manager")

        manager = await db.get(User, current_user.manager_id)
        if not manager:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reporting manager not found")

        previous_progress = float(goal.progress or 0.0)
        proposed_start, proposed_end = await CheckinService._find_best_slot(current_user, manager)
        checkin = Checkin(
            goal_id=payload.goal_id,
            employee_id=current_user.id,
            manager_id=current_user.manager_id,
            progress=payload.progress,
            status=CheckinStatus.submitted,
            meeting_date=proposed_start,
            summary=payload.summary,
            blockers=payload.blockers,
            next_steps=payload.next_steps,
        )
        goal.progress = payload.progress
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

        insights = CheckinService._generate_insights(
            previous_progress=previous_progress,
            current_progress=payload.progress,
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
                Checkin.goal_id,
                Goal.title,
                Checkin.progress,
                Checkin.summary,
                Checkin.blockers,
                Checkin.next_steps,
                Checkin.status,
                Checkin.created_at,
            )
            .join(User, User.id == Checkin.employee_id)
            .join(Goal, Goal.id == Checkin.goal_id)
            .where(
                Checkin.manager_id == current_user.id,
                Checkin.status == CheckinStatus.submitted,
            )
            .order_by(Checkin.created_at.desc())
        )
        result = await db.execute(stmt)
        return [
            {
                "id": row[0],
                "employee_id": row[1],
                "employee_name": row[2],
                "goal_id": row[3],
                "goal_title": row[4],
                "progress": row[5],
                "summary": row[6],
                "blockers": row[7],
                "next_steps": row[8],
                "status": row[9],
                "created_at": row[10],
            }
            for row in result.all()
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

        if payload.status != CheckinStatus.reviewed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager can only set status to reviewed")

        checkin.manager_feedback = payload.manager_feedback
        checkin.status = CheckinStatus.reviewed
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

        rating = CheckinRating(
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
        return rating

    @staticmethod
    async def get_employee_final_rating(employee_id: str, current_user: User, db: AsyncSession) -> tuple[float, int]:
        if current_user.role == UserRole.employee and str(current_user.id) != str(employee_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this final rating")

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
