from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.integrations.google.meet_service import MeetService
from app.models.user import User
from app.schemas.meeting import (
    AvailabilityResponse,
    MeetingCreateRequest,
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
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> list[MeetingOut]:
    service = MeetService(google_access_token)
    meetings = await service.list_meetings(current_user, db)
    return [MeetingOut.model_validate(meeting) for meeting in meetings]


@router.get("/meetings/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    service = MeetService(google_access_token)
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
    google_access_token: str = Depends(get_google_access_token),
    db: AsyncSession = Depends(get_db),
) -> MeetingsAnalyticsResponse:
    service = MeetService(google_access_token)
    payload = await service.analytics(current_user, db)
    return MeetingsAnalyticsResponse(**payload)
