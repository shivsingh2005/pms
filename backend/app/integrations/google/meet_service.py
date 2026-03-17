from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import cache_get, cache_set
from app.integrations.google.calendar_client import GoogleCalendarAPIError, GoogleCalendarAuthError
from app.integrations.google.calendar_service import CalendarService
from app.ai.ai_service import AIService
from app.models.checkin import Checkin
from app.models.enums import MeetingStatus, UserRole
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.meeting import MeetingCreateRequest, MeetingUpdateRequest


class MeetService:
    def __init__(self, access_token: str | None = None):
        self._access_token = access_token
        self._calendar_service: CalendarService | None = None

    @property
    def calendar_service(self) -> CalendarService:
        if self._calendar_service is not None:
            return self._calendar_service
        if not self._access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Calendar is not connected for this account",
            )
        self._calendar_service = CalendarService(self._access_token)
        return self._calendar_service

    @staticmethod
    def _validate_create_role(user: User) -> None:
        if user.role not in {UserRole.employee, UserRole.manager, UserRole.admin}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create meetings")

    @staticmethod
    def _ensure_meeting_access(current_user: User, meeting: Meeting, organizer_manager_id: UUID | None = None) -> None:
        if current_user.role in {UserRole.hr, UserRole.admin}:
            return
        if current_user.role == UserRole.employee and meeting.organizer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Meeting access denied")
        if current_user.role == UserRole.manager:
            if meeting.organizer_id == current_user.id:
                return
            if organizer_manager_id == current_user.id:
                return
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Meeting access denied")

    async def get_availability(
        self,
        participants_emails: list[str],
        start_time: datetime,
        end_time: datetime,
        slot_minutes: int,
    ) -> list[dict[str, str]]:
        try:
            return await self.calendar_service.get_available_slots(
                participants_emails=participants_emails,
                start_time=start_time,
                end_time=end_time,
                slot_minutes=slot_minutes,
            )
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    async def create_meeting(self, current_user: User, payload: MeetingCreateRequest, db: AsyncSession) -> Meeting:
        self._validate_create_role(current_user)

        goal_result = await db.execute(select(Goal).where(Goal.id == payload.goal_id))
        goal = goal_result.scalar_one_or_none()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        if current_user.role == UserRole.employee and goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create meeting for this goal")

        try:
            event = await self.calendar_service.client.create_event(
                title=payload.title,
                description=payload.description,
                start_time_iso=payload.start_time.astimezone(timezone.utc).isoformat(),
                end_time_iso=payload.end_time.astimezone(timezone.utc).isoformat(),
                participants=payload.participants,
            )
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        google_event_id = event.get("id")
        if not google_event_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google Calendar returned an invalid event response (missing event id)",
            )

        conference_data = event.get("conferenceData") or {}
        entry_points = conference_data.get("entryPoints") or []
        conference_uri = next(
            (
                entry.get("uri")
                for entry in entry_points
                if isinstance(entry, dict) and entry.get("uri")
            ),
            None,
        )

        meeting = Meeting(
            title=payload.title,
            description=payload.description,
            organizer_id=current_user.id,
            goal_id=payload.goal_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            google_event_id=google_event_id,
            google_meet_link=event.get("hangoutLink") or conference_uri,
            participants=payload.participants,
            status=MeetingStatus.scheduled,
        )
        db.add(meeting)
        try:
            await db.commit()
        except DataError as exc:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meeting payload") from exc
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Meeting could not be created due to a data conflict") from exc
        await db.refresh(meeting)
        return meeting

    async def list_meetings(self, current_user: User, db: AsyncSession) -> list[Meeting]:
        stmt = select(Meeting)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(Meeting.organizer_id == current_user.id)
        elif current_user.role == UserRole.manager:
            stmt = stmt.join(User, Meeting.organizer_id == User.id).where(
                (Meeting.organizer_id == current_user.id) | (User.manager_id == current_user.id)
            )
        elif current_user.role in {UserRole.hr, UserRole.admin}:
            stmt = stmt.join(User, Meeting.organizer_id == User.id).where(User.organization_id == current_user.organization_id)
        else:
            stmt = stmt.where(Meeting.organizer_id == current_user.id)
        result = await db.execute(stmt.order_by(Meeting.start_time.desc()))
        return list(result.scalars().all())

    async def get_meeting(self, meeting_id: str, current_user: User, db: AsyncSession) -> Meeting:
        try:
            meeting_uuid = UUID(meeting_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meeting id") from exc

        stmt = select(Meeting, User.manager_id).join(User, Meeting.organizer_id == User.id).where(Meeting.id == meeting_uuid)
        result = await db.execute(stmt)
        record = result.first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        meeting, organizer_manager_id = record
        self._ensure_meeting_access(current_user, meeting, organizer_manager_id)
        return meeting

    async def update_meeting(
        self,
        meeting_id: str,
        payload: MeetingUpdateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> Meeting:
        meeting = await self.get_meeting(meeting_id, current_user, db)
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.admin}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update meeting")

        try:
            event = await self.calendar_service.client.update_event(
                google_event_id=meeting.google_event_id,
                title=payload.title,
                description=payload.description,
                start_time_iso=payload.start_time.astimezone(timezone.utc).isoformat() if payload.start_time else None,
                end_time_iso=payload.end_time.astimezone(timezone.utc).isoformat() if payload.end_time else None,
                participants=payload.participants,
            )
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(meeting, field, value)

        meeting.google_meet_link = event.get("hangoutLink") or meeting.google_meet_link
        await db.commit()
        await db.refresh(meeting)
        return meeting

    async def cancel_meeting(self, meeting_id: str, current_user: User, db: AsyncSession) -> Meeting:
        meeting = await self.get_meeting(meeting_id, current_user, db)
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.admin}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to cancel meeting")

        try:
            await self.calendar_service.client.delete_event(meeting.google_event_id)
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        meeting.status = MeetingStatus.cancelled
        await db.commit()
        await db.refresh(meeting)
        return meeting

    async def sync_transcript(self, meeting_id: str, current_user: User, db: AsyncSession) -> dict:
        meeting = await self.get_meeting(meeting_id, current_user, db)

        try:
            event = await self.calendar_service.client.get_event(meeting.google_event_id)
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        attachments = event.get("attachments", [])
        transcript = None
        for attachment in attachments:
            title = (attachment.get("title") or "").lower()
            if "transcript" in title:
                transcript = attachment.get("fileUrl") or attachment.get("title")
                break

        if not transcript:
            transcript = "Transcript is not yet available from Google Meet artifacts"

        stmt = select(Checkin).where(Checkin.goal_id == meeting.goal_id).order_by(Checkin.meeting_date.desc()).limit(1)
        checkin_result = await db.execute(stmt)
        checkin = checkin_result.scalar_one_or_none()
        if checkin:
            checkin.transcript = transcript
            checkin.meeting_link = meeting.google_meet_link

        meeting.status = MeetingStatus.completed
        await db.commit()

        return {
            "meeting_id": str(meeting.id),
            "goal_id": str(meeting.goal_id),
            "transcript": transcript,
            "checkin_synced": checkin is not None,
        }

    async def analytics(self, current_user: User, db: AsyncSession) -> dict:
        if current_user.role not in {UserRole.leadership, UserRole.hr, UserRole.admin}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view analytics")

        cache_key = f"meetings:analytics:{current_user.organization_id}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        stmt = select(
            func.count(Meeting.id),
            func.sum(case((Meeting.status == MeetingStatus.completed, 1), else_=0)),
            func.sum(case((Meeting.status == MeetingStatus.cancelled, 1), else_=0)),
        )
        result = await db.execute(stmt)
        total, completed, cancelled = result.one()
        payload = {
            "total_meetings": int(total or 0),
            "completed_meetings": int(completed or 0),
            "cancelled_meetings": int(cancelled or 0),
        }
        await cache_set(cache_key, payload)
        return payload

    async def summarize_meeting(self, meeting_id: str, current_user: User, db: AsyncSession) -> dict:
        meeting = await self.get_meeting(meeting_id, current_user, db)

        stmt = select(Checkin).where(Checkin.goal_id == meeting.goal_id).order_by(Checkin.meeting_date.desc())
        result = await db.execute(stmt)
        checkins = list(result.scalars().all())

        linked_checkin = None
        for item in checkins:
            if (item.meeting_link or "").strip() == (meeting.google_meet_link or "").strip():
                linked_checkin = item
                break
        if linked_checkin is None and checkins:
            linked_checkin = checkins[0]

        if linked_checkin is None:
            return {
                "meeting_id": str(meeting.id),
                "summary": "Meeting not started yet",
                "key_points": [],
                "action_items": [],
            }

        transcript = (linked_checkin.transcript or "").strip()
        if not transcript:
            summary_notes = (linked_checkin.summary or "").strip()
            if summary_notes:
                transcript = f"Meeting notes:\n{summary_notes}"

        if not transcript:
            return {
                "meeting_id": str(meeting.id),
                "summary": "Meeting not started yet",
                "key_points": [],
                "action_items": [],
            }

        ai_service = AIService()
        ai_payload = await ai_service.summarize_checkin_transcript(current_user, transcript, db)

        ai_summary = str(ai_payload.get("summary") or "").strip()
        if ai_summary:
            linked_checkin.summary = ai_summary
            await db.commit()

        return {
            "meeting_id": str(meeting.id),
            "summary": ai_summary or "Summary unavailable",
            "key_points": list(ai_payload.get("key_points") or []),
            "action_items": list(ai_payload.get("action_items") or []),
        }
