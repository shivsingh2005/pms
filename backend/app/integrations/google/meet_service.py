from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import case, func, select, text
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
from app.services.cycle_guard import ensure_cycle_writable
from app.schemas.meeting import MeetingCreateRequest, MeetingUpdateRequest


class MeetService:
    logger = logging.getLogger(__name__)

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
        if user.role not in {UserRole.employee, UserRole.manager, UserRole.hr}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create meetings")

    @staticmethod
    def _ensure_meeting_access(current_user: User, meeting: Meeting, organizer_manager_id: UUID | None = None) -> None:
        if current_user.role in {UserRole.hr, UserRole.leadership}:
            return
        if current_user.role == UserRole.employee and meeting.organizer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Meeting access denied")
        if current_user.role == UserRole.manager:
            if meeting.organizer_id == current_user.id:
                return
            if organizer_manager_id == current_user.id:
                return
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Meeting access denied")

    @staticmethod
    def _proposal_to_api_payload(proposal: MeetingProposal, meeting: Meeting) -> dict:
        proposed_start_time = proposal.scheduled_at or meeting.start_time
        meeting_duration = meeting.end_time - meeting.start_time
        if meeting_duration.total_seconds() <= 0:
            meeting_duration = timedelta(minutes=30)
        proposed_end_time = proposed_start_time + meeting_duration

        return {
            "id": proposal.id,
            "checkin_id": meeting.checkin_id,
            "employee_id": meeting.employee_id,
            "manager_id": meeting.manager_id,
            "proposed_start_time": proposed_start_time,
            "proposed_end_time": proposed_end_time,
            "status": proposal.status,
            "created_at": proposal.created_at,
        }

    @staticmethod
    def _proposal_payload_from_values(
        proposal_id: UUID | str,
        checkin_id: UUID | str | None,
        employee_id: UUID | str | None,
        manager_id: UUID | str | None,
        proposed_start_time: datetime,
        proposed_end_time: datetime,
        status_value: str,
        created_at: datetime,
    ) -> dict:
        return {
            "id": proposal_id,
            "checkin_id": checkin_id,
            "employee_id": employee_id,
            "manager_id": manager_id,
            "proposed_start_time": proposed_start_time,
            "proposed_end_time": proposed_end_time,
            "status": status_value,
            "created_at": created_at,
        }

    async def _meeting_proposal_columns(self, db: AsyncSession) -> set[str]:
        result = await db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'meeting_proposals'
                """
            )
        )
        return {str(row[0]) for row in result.all()}

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
        if meeting_type == MeetingType.CHECKIN and payload.checkin_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkin_id is required for CHECKIN meetings")

        linked_checkin: Checkin | None = None
        if payload.checkin_id is not None:
            linked_checkin = await db.get(Checkin, payload.checkin_id)
            if not linked_checkin:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")
            await ensure_cycle_writable(db, linked_checkin.cycle_id, locked_detail="Cannot create meeting in a locked cycle")

        selected_goal_ids: list[UUID] = []
        if meeting_type == MeetingType.CHECKIN and linked_checkin is not None:
            allowed_goal_ids = set(linked_checkin.goal_ids or [])
            requested_goal_ids = list(dict.fromkeys(payload.goal_ids or []))

            if requested_goal_ids:
                invalid_goal_ids = [goal_id for goal_id in requested_goal_ids if goal_id not in allowed_goal_ids]
                if invalid_goal_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more selected goals are not linked to the selected check-in",
                    )
                selected_goal_ids = requested_goal_ids
            else:
                selected_goal_ids = list(allowed_goal_ids)

        goal: Goal | None = None
        if payload.goal_id is not None and meeting_type != MeetingType.CHECKIN:
            goal_result = await db.execute(select(Goal).where(Goal.id == payload.goal_id))
            goal = goal_result.scalar_one_or_none()
            if not goal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
            await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot create meeting in a locked cycle")

        resolved_employee_id = payload.employee_id or (linked_checkin.employee_id if linked_checkin else None) or (goal.user_id if goal else None)
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

        if meeting_type == MeetingType.CHECKIN and linked_checkin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CHECKIN meetings require a valid checkin_id")

        if meeting_type == MeetingType.CHECKIN and employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CHECKIN meetings require a target employee")

        if linked_checkin is not None and employee is not None and linked_checkin.employee_id != employee.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in does not belong to selected employee")

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
            checkin_id=linked_checkin.id if linked_checkin else None,
            cycle_id=(linked_checkin.cycle_id if linked_checkin else (goal.cycle_id if goal else None)),
            employee_id=employee.id if employee else None,
            manager_id=manager.id if manager else None,
            meeting_type=meeting_type,
            goal_id=goal.id if goal else (selected_goal_ids[0] if selected_goal_ids else None),
            start_time=payload.start_time,
            end_time=payload.end_time,
            google_event_id=google_event_id,
            meet_link=event.get("hangoutLink") or conference_uri,
            google_meet_link=event.get("hangoutLink") or conference_uri,
            goal_discussion_notes={
                "goal_ids": [str(goal_id) for goal_id in selected_goal_ids]
            } if selected_goal_ids else {},
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
        MeetService.logger.info(
            "Meeting created",
            extra={
                "meeting_id": str(meeting.id),
                "organizer_id": str(meeting.organizer_id),
                "employee_id": str(meeting.employee_id) if meeting.employee_id else None,
                "manager_id": str(meeting.manager_id) if meeting.manager_id else None,
                "cycle_id": str(meeting.cycle_id) if meeting.cycle_id else None,
                "meeting_type": meeting.meeting_type.value if hasattr(meeting.meeting_type, "value") else str(meeting.meeting_type),
            },
        )
        return meeting

    async def list_pending_proposals(self, current_user: User, db: AsyncSession) -> list[dict]:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can access meeting proposals")

        columns = await self._meeting_proposal_columns(db)

        if "meeting_id" in columns:
            result = await db.execute(
                text(
                    """
                    SELECT
                        mp.id,
                        m.checkin_id,
                        m.employee_id,
                        m.manager_id,
                        COALESCE(mp.scheduled_at, m.start_time) AS proposed_start_time,
                        (COALESCE(mp.scheduled_at, m.start_time) + (m.end_time - m.start_time)) AS proposed_end_time,
                        mp.status,
                        mp.created_at
                    FROM meeting_proposals mp
                    JOIN meetings m ON m.id = mp.meeting_id
                    WHERE m.manager_id = :manager_id
                      AND mp.status = :proposal_status
                    ORDER BY mp.created_at DESC
                    """
                ),
                {
                    "manager_id": current_user.id,
                    "proposal_status": MeetingProposalStatus.pending.value,
                },
            )
        else:
            result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        checkin_id,
                        employee_id,
                        manager_id,
                        proposed_start_time,
                        proposed_end_time,
                        status,
                        created_at
                    FROM meeting_proposals
                    WHERE manager_id = :manager_id
                      AND status = :proposal_status
                    ORDER BY created_at DESC
                    """
                ),
                {
                    "manager_id": current_user.id,
                    "proposal_status": MeetingProposalStatus.pending.value,
                },
            )

        return [
            self._proposal_payload_from_values(
                proposal_id=row["id"],
                checkin_id=row["checkin_id"],
                employee_id=row["employee_id"],
                manager_id=row["manager_id"],
                proposed_start_time=row["proposed_start_time"],
                proposed_end_time=row["proposed_end_time"],
                status_value=row["status"],
                created_at=row["created_at"],
            )
            for row in result.mappings().all()
        ]

    async def approve_proposal(self, proposal_id: str, current_user: User, db: AsyncSession) -> tuple[dict, Meeting]:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can approve meeting proposals")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        columns = await self._meeting_proposal_columns(db)
        is_new_schema = "meeting_id" in columns

        if is_new_schema:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        mp.id,
                        mp.status,
                        mp.created_at,
                        m.id AS meeting_id,
                        m.checkin_id,
                        m.employee_id,
                        m.manager_id,
                        COALESCE(mp.scheduled_at, m.start_time) AS proposed_start_time,
                        (COALESCE(mp.scheduled_at, m.start_time) + (m.end_time - m.start_time)) AS proposed_end_time
                    FROM meeting_proposals mp
                    JOIN meetings m ON m.id = mp.meeting_id
                    WHERE mp.id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )
            proposal_row = proposal_result.mappings().first()
            if not proposal_row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")
            if proposal_row["manager_id"] != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to approve this proposal")
            if proposal_row["status"] != MeetingProposalStatus.pending.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal is not pending")

            meeting = await db.get(Meeting, proposal_row["meeting_id"])
            if not meeting:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related meeting not found")
        else:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        checkin_id,
                        employee_id,
                        manager_id,
                        proposed_start_time,
                        proposed_end_time,
                        status,
                        created_at
                    FROM meeting_proposals
                    WHERE id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )
            proposal_row = proposal_result.mappings().first()
            if not proposal_row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")
            if proposal_row["manager_id"] != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to approve this proposal")
            if proposal_row["status"] != MeetingProposalStatus.pending.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal is not pending")

            meeting = None

        checkin_id = proposal_row["checkin_id"]
        employee_id = proposal_row["employee_id"]
        proposed_start_time = proposal_row["proposed_start_time"]
        proposed_end_time = proposal_row["proposed_end_time"]

        checkin = await db.get(Checkin, checkin_id) if checkin_id else None
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related check-in not found")
        await ensure_cycle_writable(db, checkin.cycle_id, locked_detail="Cannot approve proposal in a locked cycle")

        employee = await db.get(User, employee_id) if employee_id else None
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if not employee.email or not current_user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing participant email for scheduling")

        start_iso = proposed_start_time.astimezone(timezone.utc).isoformat()
        end_iso = proposed_end_time.astimezone(timezone.utc).isoformat()

        try:
            event = await self.calendar_service.client.create_event(
                title=f"Check-in: {employee.name}",
                description=f"Unified check-in discussion for {employee.name}",
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

        if is_new_schema:
            meeting.start_time = proposed_start_time
            meeting.end_time = proposed_end_time
            meeting.google_event_id = google_event_id
            meeting.meet_link = meet_link
            meeting.google_meet_link = meet_link
            meeting.participants = [employee.email, current_user.email]
            meeting.status = MeetingStatus.scheduled
        else:
            meeting = Meeting(
                title=f"Check-in: {employee.name}",
                description=f"Scheduled from manager approval for check-in {checkin.id}",
                organizer_id=current_user.id,
                checkin_id=checkin.id,
                cycle_id=checkin.cycle_id,
                employee_id=employee.id,
                manager_id=current_user.id,
                meeting_type=MeetingType.CHECKIN,
                goal_id=None,
                start_time=proposed_start_time,
                end_time=proposed_end_time,
                google_event_id=google_event_id,
                meet_link=meet_link,
                google_meet_link=meet_link,
                participants=[employee.email, current_user.email],
                status=MeetingStatus.scheduled,
            )
            db.add(meeting)

        if is_new_schema:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET status = :proposal_status,
                        is_accepted = true
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "proposal_status": MeetingProposalStatus.approved.value,
                    "proposal_id": proposal_uuid,
                },
            )
        else:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET status = :proposal_status
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "proposal_status": MeetingProposalStatus.approved.value,
                    "proposal_id": proposal_uuid,
                },
            )

        checkin.meeting_date = proposed_start_time
        checkin.meeting_link = meet_link

        await db.commit()
        await db.refresh(meeting)
        MeetService.logger.info(
            "Meeting proposal approved and meeting scheduled",
            extra={
                "proposal_id": str(proposal_uuid),
                "meeting_id": str(meeting.id),
                "checkin_id": str(checkin.id),
                "cycle_id": str(meeting.cycle_id) if meeting.cycle_id else None,
            },
        )
        return (
            self._proposal_payload_from_values(
                proposal_id=proposal_uuid,
                checkin_id=checkin_id,
                employee_id=employee_id,
                manager_id=current_user.id,
                proposed_start_time=proposed_start_time,
                proposed_end_time=proposed_end_time,
                status_value=MeetingProposalStatus.approved.value,
                created_at=proposal_row["created_at"],
            ),
            meeting,
        )

    async def reject_proposal(
        self,
        proposal_id: str,
        current_user: User,
        db: AsyncSession,
        suggest_new_start_time: datetime | None = None,
    ) -> dict:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reject meeting proposals")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        columns = await self._meeting_proposal_columns(db)
        is_new_schema = "meeting_id" in columns

        if is_new_schema:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        mp.id,
                        mp.status,
                        mp.created_at,
                        m.checkin_id,
                        m.employee_id,
                        m.manager_id,
                        COALESCE(mp.scheduled_at, m.start_time) AS proposed_start_time,
                        (COALESCE(mp.scheduled_at, m.start_time) + (m.end_time - m.start_time)) AS proposed_end_time
                    FROM meeting_proposals mp
                    JOIN meetings m ON m.id = mp.meeting_id
                    WHERE mp.id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )
        else:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        status,
                        created_at,
                        checkin_id,
                        employee_id,
                        manager_id,
                        proposed_start_time,
                        proposed_end_time
                    FROM meeting_proposals
                    WHERE id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )

        proposal_row = proposal_result.mappings().first()
        if not proposal_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")

        if proposal_row["manager_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to reject this proposal")

        checkin = await db.get(Checkin, proposal_row["checkin_id"]) if proposal_row["checkin_id"] else None
        if checkin:
            await ensure_cycle_writable(db, checkin.cycle_id, locked_detail="Cannot reject proposal in a locked cycle")

        update_start = proposal_row["proposed_start_time"]
        update_end = proposal_row["proposed_end_time"]
        if suggest_new_start_time is not None:
            duration = update_end - update_start
            if duration.total_seconds() <= 0:
                duration = timedelta(minutes=30)
            update_start = suggest_new_start_time
            update_end = suggest_new_start_time + duration

        if is_new_schema:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET status = :proposal_status,
                        is_accepted = false,
                        scheduled_at = :scheduled_at,
                        reason = :reason
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "proposal_status": MeetingProposalStatus.rejected.value,
                    "scheduled_at": update_start,
                    "reason": "Manager suggested a new slot" if suggest_new_start_time is not None else None,
                    "proposal_id": proposal_uuid,
                },
            )
        else:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET status = :proposal_status,
                        proposed_start_time = :proposed_start_time,
                        proposed_end_time = :proposed_end_time
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "proposal_status": MeetingProposalStatus.rejected.value,
                    "proposed_start_time": update_start,
                    "proposed_end_time": update_end,
                    "proposal_id": proposal_uuid,
                },
            )

        await db.commit()
        return self._proposal_payload_from_values(
            proposal_id=proposal_uuid,
            checkin_id=proposal_row["checkin_id"],
            employee_id=proposal_row["employee_id"],
            manager_id=proposal_row["manager_id"],
            proposed_start_time=update_start,
            proposed_end_time=update_end,
            status_value=MeetingProposalStatus.rejected.value,
            created_at=proposal_row["created_at"],
        )

    async def reschedule_proposal(
        self,
        proposal_id: str,
        current_user: User,
        db: AsyncSession,
        proposed_start_time: datetime,
        proposed_end_time: datetime,
    ) -> dict:
        if current_user.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reschedule meeting proposals")

        if proposed_end_time <= proposed_start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

        try:
            proposal_uuid = UUID(proposal_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposal id") from exc

        columns = await self._meeting_proposal_columns(db)
        is_new_schema = "meeting_id" in columns

        if is_new_schema:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        mp.id,
                        mp.status,
                        mp.created_at,
                        m.checkin_id,
                        m.employee_id,
                        m.manager_id
                    FROM meeting_proposals mp
                    JOIN meetings m ON m.id = mp.meeting_id
                    WHERE mp.id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )
        else:
            proposal_result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        status,
                        created_at,
                        checkin_id,
                        employee_id,
                        manager_id
                    FROM meeting_proposals
                    WHERE id = :proposal_id
                    """
                ),
                {"proposal_id": proposal_uuid},
            )

        proposal_row = proposal_result.mappings().first()
        if not proposal_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found")

        if proposal_row["manager_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to reschedule this proposal")

        if proposal_row["status"] != MeetingProposalStatus.pending.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending proposals can be rescheduled")

        checkin = await db.get(Checkin, proposal_row["checkin_id"]) if proposal_row["checkin_id"] else None
        if checkin:
            await ensure_cycle_writable(db, checkin.cycle_id, locked_detail="Cannot reschedule proposal in a locked cycle")

        if is_new_schema:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET scheduled_at = :scheduled_at,
                        reason = :reason
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "scheduled_at": proposed_start_time,
                    "reason": f"Rescheduled by manager to end at {proposed_end_time.isoformat()}",
                    "proposal_id": proposal_uuid,
                },
            )
        else:
            await db.execute(
                text(
                    """
                    UPDATE meeting_proposals
                    SET proposed_start_time = :proposed_start_time,
                        proposed_end_time = :proposed_end_time
                    WHERE id = :proposal_id
                    """
                ),
                {
                    "proposed_start_time": proposed_start_time,
                    "proposed_end_time": proposed_end_time,
                    "proposal_id": proposal_uuid,
                },
            )

        await db.commit()
        return self._proposal_payload_from_values(
            proposal_id=proposal_uuid,
            checkin_id=proposal_row["checkin_id"],
            employee_id=proposal_row["employee_id"],
            manager_id=proposal_row["manager_id"],
            proposed_start_time=proposed_start_time,
            proposed_end_time=proposed_end_time,
            status_value=MeetingProposalStatus.pending.value,
            created_at=proposal_row["created_at"],
        )

    async def list_meetings(self, current_user: User, db: AsyncSession) -> list[Meeting]:
        stmt = select(Meeting)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(Meeting.organizer_id == current_user.id)
        elif current_user.role == UserRole.manager:
            stmt = stmt.join(User, Meeting.organizer_id == User.id).where(
                (Meeting.organizer_id == current_user.id) | (User.manager_id == current_user.id)
            )
        elif current_user.role in {UserRole.hr, UserRole.leadership}:
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
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.hr, UserRole.leadership}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update meeting")
        await ensure_cycle_writable(db, meeting.cycle_id, locked_detail="Cannot update meeting in a locked cycle")

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
        if current_user.role not in {UserRole.manager, UserRole.employee, UserRole.hr, UserRole.leadership}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to cancel meeting")
        await ensure_cycle_writable(db, meeting.cycle_id, locked_detail="Cannot cancel meeting in a locked cycle")

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

        checkin = await db.get(Checkin, meeting.checkin_id) if meeting.checkin_id else None
        if checkin:
            checkin.transcript = transcript
            checkin.meeting_link = meeting.meet_link or meeting.google_meet_link

        meeting.status = MeetingStatus.completed
        await db.commit()

        return {
            "meeting_id": str(meeting.id),
            "checkin_id": str(meeting.checkin_id) if meeting.checkin_id else None,
            "transcript": transcript,
            "checkin_synced": checkin is not None,
        }

    async def analytics(self, current_user: User, db: AsyncSession) -> dict:
        if current_user.role not in {UserRole.leadership, UserRole.hr}:
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

        if meeting.checkin_id is None:
            return {
                "meeting_id": str(meeting.id),
                "summary": "Meeting not started yet",
                "key_points": [],
                "action_items": [],
            }

        linked_checkin = await db.get(Checkin, meeting.checkin_id)

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
