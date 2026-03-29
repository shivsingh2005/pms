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
from app.models.enums import MeetingProposalStatus, MeetingStatus, MeetingType, UserRole
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.meeting_proposal import MeetingProposal
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
        if user.role not in {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.admin}:
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

        meeting_type = payload.meeting_type
        if meeting_type == MeetingType.CHECKIN and payload.goal_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="goal_id is required for CHECKIN meetings")

        goal: Goal | None = None
        if payload.goal_id is not None:
            goal_result = await db.execute(select(Goal).where(Goal.id == payload.goal_id))
            goal = goal_result.scalar_one_or_none()
            if not goal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        resolved_employee_id = payload.employee_id or (goal.user_id if goal else None)
        if resolved_employee_id is None and current_user.role == UserRole.employee:
            resolved_employee_id = current_user.id

        employee: User | None = None
        if resolved_employee_id is not None:
            employee = await db.get(User, resolved_employee_id)
            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

            if current_user.role == UserRole.employee and employee.id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create meeting for this employee")

            if current_user.organization_id != employee.organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee must be in the same organization")

        if meeting_type == MeetingType.CHECKIN and goal is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CHECKIN meetings require a valid goal_id")

        if meeting_type == MeetingType.CHECKIN and employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CHECKIN meetings require a target employee")

        if goal is not None and employee is not None and goal.user_id != employee.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal does not belong to selected employee")

        manager: User | None = None
        if payload.manager_id is not None:
            manager = await db.get(User, payload.manager_id)
            if not manager:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
        elif current_user.role == UserRole.manager:
            manager = current_user
        elif employee and employee.manager_id:
            manager = await db.get(User, employee.manager_id)

        if manager and manager.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager must be in the same organization")

        participant_set = {email.strip().lower() for email in payload.participants if email and email.strip()}
        if employee and employee.email:
            participant_set.add(employee.email.strip().lower())
        if manager and manager.email:
            participant_set.add(manager.email.strip().lower())
        if current_user.email:
            participant_set.add(current_user.email.strip().lower())

        if not participant_set:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one participant is required")

        participants = sorted(participant_set)

        try:
            event = await self.calendar_service.client.create_event(
                title=payload.title,
                description=payload.description,
                start_time_iso=payload.start_time.astimezone(timezone.utc).isoformat(),
                end_time_iso=payload.end_time.astimezone(timezone.utc).isoformat(),
                participants=participants,
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
            checkin_id=None,
            employee_id=employee.id if employee else None,
            manager_id=manager.id if manager else None,
            meeting_type=meeting_type,
            goal_id=goal.id if goal else None,
            start_time=payload.start_time,
            end_time=payload.end_time,
            google_event_id=google_event_id,
            meet_link=event.get("hangoutLink") or conference_uri,
            google_meet_link=event.get("hangoutLink") or conference_uri,
            participants=participants,
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

    async def list_pending_proposals(self, current_user: User, db: AsyncSession) -> list[MeetingProposal]:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can access meeting proposals")

        result = await db.execute(
            select(MeetingProposal)
            .where(
                MeetingProposal.manager_id == current_user.id,
                MeetingProposal.status == MeetingProposalStatus.pending,
            )
            .order_by(MeetingProposal.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve_proposal(self, proposal_id: str, current_user: User, db: AsyncSession) -> tuple[MeetingProposal, Meeting]:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can approve meeting proposals")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        proposal = await db.get(MeetingProposal, proposal_uuid)
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")

        if proposal.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to approve this proposal")

        if proposal.status != MeetingProposalStatus.pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal is not pending")

        checkin = await db.get(Checkin, proposal.checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related check-in not found")

        employee = await db.get(User, proposal.employee_id)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if not employee.email or not current_user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing participant email for scheduling")

        start_iso = proposal.proposed_start_time.astimezone(timezone.utc).isoformat()
        end_iso = proposal.proposed_end_time.astimezone(timezone.utc).isoformat()

        try:
            event = await self.calendar_service.client.create_event(
                title=f"Check-in: {employee.name}",
                description=f"Check-in discussion for goal {checkin.goal_id}",
                start_time_iso=start_iso,
                end_time_iso=end_iso,
                participants=[employee.email, current_user.email],
            )
        except GoogleCalendarAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except GoogleCalendarAPIError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        google_event_id = event.get("id")
        if not google_event_id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Calendar did not return event id")

        conference_data = event.get("conferenceData") or {}
        entry_points = conference_data.get("entryPoints") or []
        conference_uri = next(
            (entry.get("uri") for entry in entry_points if isinstance(entry, dict) and entry.get("uri")),
            None,
        )
        meet_link = event.get("hangoutLink") or conference_uri

        meeting = Meeting(
            title=f"Check-in: {employee.name}",
            description=f"Scheduled from manager approval for check-in {checkin.id}",
            organizer_id=current_user.id,
            checkin_id=checkin.id,
            employee_id=proposal.employee_id,
            manager_id=proposal.manager_id,
            meeting_type=MeetingType.CHECKIN,
            goal_id=checkin.goal_id,
            start_time=proposal.proposed_start_time,
            end_time=proposal.proposed_end_time,
            google_event_id=google_event_id,
            meet_link=meet_link,
            google_meet_link=meet_link,
            participants=[employee.email, current_user.email],
            status=MeetingStatus.scheduled,
        )
        db.add(meeting)

        proposal.status = MeetingProposalStatus.approved
        checkin.meeting_date = proposal.proposed_start_time
        checkin.meeting_link = meet_link

        await db.commit()
        await db.refresh(meeting)
        await db.refresh(proposal)
        return proposal, meeting

    async def reject_proposal(
        self,
        proposal_id: str,
        current_user: User,
        db: AsyncSession,
        suggest_new_start_time: datetime | None = None,
    ) -> MeetingProposal:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reject meeting proposals")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        proposal = await db.get(MeetingProposal, proposal_uuid)
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")

        if proposal.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to reject this proposal")

        proposal.status = MeetingProposalStatus.rejected
        if suggest_new_start_time is not None:
            duration = proposal.proposed_end_time - proposal.proposed_start_time
            proposal.proposed_start_time = suggest_new_start_time
            proposal.proposed_end_time = suggest_new_start_time + duration

        await db.commit()
        await db.refresh(proposal)
        return proposal

    async def reschedule_proposal(
        self,
        proposal_id: str,
        current_user: User,
        db: AsyncSession,
        proposed_start_time: datetime,
        proposed_end_time: datetime,
    ) -> MeetingProposal:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reschedule meeting proposals")

        if proposed_end_time <= proposed_start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        proposal = await db.get(MeetingProposal, proposal_uuid)
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")

        if proposal.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to reschedule this proposal")

        if proposal.status != MeetingProposalStatus.pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending proposals can be rescheduled")

        proposal.proposed_start_time = proposed_start_time
        proposal.proposed_end_time = proposed_end_time

        await db.commit()
        await db.refresh(proposal)
        return proposal

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
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.hr, UserRole.admin}:
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

        refreshed_link = event.get("hangoutLink") or meeting.google_meet_link
        meeting.google_meet_link = refreshed_link
        meeting.meet_link = refreshed_link
        await db.commit()
        await db.refresh(meeting)
        return meeting

    async def cancel_meeting(self, meeting_id: str, current_user: User, db: AsyncSession) -> Meeting:
        meeting = await self.get_meeting(meeting_id, current_user, db)
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.hr, UserRole.admin}:
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

        checkin = None
        if meeting.goal_id is not None:
            stmt = select(Checkin).where(Checkin.goal_id == meeting.goal_id).order_by(Checkin.meeting_date.desc()).limit(1)
            checkin_result = await db.execute(stmt)
            checkin = checkin_result.scalar_one_or_none()
        if checkin:
            checkin.transcript = transcript
            checkin.meeting_link = meeting.meet_link or meeting.google_meet_link

        meeting.status = MeetingStatus.completed
        await db.commit()

        return {
            "meeting_id": str(meeting.id),
            "goal_id": str(meeting.goal_id) if meeting.goal_id else None,
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

        if meeting.goal_id is None:
            return {
                "meeting_id": str(meeting.id),
                "summary": "Meeting not started yet",
                "key_points": [],
                "action_items": [],
            }

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
