from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.integrations.google.meet_service import MeetService
from app.models.user import User
from app.schemas.meeting import (
    AvailabilityResponse,
    MeetingAISummaryResponse,
    MeetingCreateRequest,
    MeetingProposalOut,
    MeetingProposalRejectRequest,
    MeetingProposalRescheduleRequest,
    MeetingsAnalyticsResponse,
    MeetingOut,
    MeetingUpdateRequest,
    TranscriptSyncResponse,
)
from app.utils.dependencies import get_current_user, get_google_access_token

router = APIRouter(tags=["Meetings"])


@router.get("/calendar/availability", response_model=AvailabilityResponse)
async def get_availability(
    participants_emails: list[str] = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    slot_minutes: int = Query(default=30, ge=15, le=120),
    _: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
) -> AvailabilityResponse:
    service = MeetService(google_access_token)
    slots = await service.get_availability(participants_emails, start_time, end_time, slot_minutes)
    return AvailabilityResponse(available_slots=slots)


@router.post("/meetings/create", response_model=MeetingOut)
async def create_meeting(
    payload: MeetingCreateRequest,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService(google_access_token)
    meeting = await service.create_meeting(current_user, payload, db)
    return MeetingOut.model_validate(meeting)


@router.get("/meetings", response_model=list[MeetingOut])
async def list_meetings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MeetingOut]:
    service = MeetService()
    meetings = await service.list_meetings(current_user, db)
    return [MeetingOut.model_validate(meeting) for meeting in meetings]


@router.get("/meetings/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService()
    meeting = await service.get_meeting(meeting_id, current_user, db)
    return MeetingOut.model_validate(meeting)


@router.patch("/meetings/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: str,
    payload: MeetingUpdateRequest,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService(google_access_token)
    meeting = await service.update_meeting(meeting_id, payload, current_user, db)
    return MeetingOut.model_validate(meeting)


@router.delete("/meetings/{meeting_id}", response_model=MeetingOut)
async def cancel_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService(google_access_token)
    meeting = await service.cancel_meeting(meeting_id, current_user, db)
    return MeetingOut.model_validate(meeting)


@router.post("/meetings/{meeting_id}/transcript-sync", response_model=TranscriptSyncResponse)
async def sync_transcript(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> TranscriptSyncResponse:
    service = MeetService(google_access_token)
    payload = await service.sync_transcript(meeting_id, current_user, db)
    return TranscriptSyncResponse(**payload)


@router.get("/meetings/analytics/summary", response_model=MeetingsAnalyticsResponse)
async def meetings_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingsAnalyticsResponse:
    service = MeetService()
    payload = await service.analytics(current_user, db)
    return MeetingsAnalyticsResponse(**payload)


@router.post("/meetings/{meeting_id}/ai-summary", response_model=MeetingAISummaryResponse)
async def summarize_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingAISummaryResponse:
    service = MeetService()
    payload = await service.summarize_meeting(meeting_id, current_user, db)
    return MeetingAISummaryResponse(**payload)


@router.get("/meetings/proposals/pending", response_model=list[MeetingProposalOut])
async def list_pending_meeting_proposals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MeetingProposalOut]:
    service = MeetService()
    proposals = await service.list_pending_proposals(current_user, db)
    return [MeetingProposalOut.model_validate(proposal) for proposal in proposals]


@router.post("/meetings/proposal/{proposal_id}/approve", response_model=MeetingOut)
async def approve_meeting_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService(google_access_token)
    _, meeting = await service.approve_proposal(proposal_id, current_user, db)
    return MeetingOut.model_validate(meeting)


@router.post("/meetings/proposal/{proposal_id}/reject", response_model=MeetingProposalOut)
async def reject_meeting_proposal(
    proposal_id: str,
    payload: MeetingProposalRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingProposalOut:
    service = MeetService()
    proposal = await service.reject_proposal(
        proposal_id,
        current_user,
        db,
        suggest_new_start_time=payload.suggest_new_start_time,
    )
    return MeetingProposalOut.model_validate(proposal)


@router.patch("/meetings/proposal/{proposal_id}/reschedule", response_model=MeetingProposalOut)
async def reschedule_meeting_proposal(
    proposal_id: str,
    payload: MeetingProposalRescheduleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingProposalOut:
    service = MeetService()
    proposal = await service.reschedule_proposal(
        proposal_id,
        current_user,
        db,
        proposed_start_time=payload.proposed_start_time,
        proposed_end_time=payload.proposed_end_time,
    )
    return MeetingProposalOut.model_validate(proposal)
