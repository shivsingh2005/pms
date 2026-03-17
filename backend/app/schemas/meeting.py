from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import MeetingStatus


class AvailabilityResponse(BaseModel):
    available_slots: list[dict[str, str]]


class MeetingCreateRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    participants: list[str] = Field(default_factory=list)
    goal_id: UUID


class MeetingUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    participants: list[str] | None = None


class MeetingOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    organizer_id: UUID
    goal_id: UUID
    start_time: datetime
    end_time: datetime
    google_event_id: str
    google_meet_link: str | None
    participants: list[str]
    status: MeetingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptSyncResponse(BaseModel):
    meeting_id: UUID
    goal_id: UUID
    transcript: str
    checkin_synced: bool


class MeetingsAnalyticsResponse(BaseModel):
    total_meetings: int
    completed_meetings: int
    cancelled_meetings: int


class MeetingAISummaryResponse(BaseModel):
    meeting_id: UUID
    summary: str
    key_points: list[str]
    action_items: list[str]
