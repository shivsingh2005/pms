from datetime import datetime
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
    goal_id: str


class MeetingUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    participants: list[str] | None = None


class MeetingOut(BaseModel):
    id: str
    title: str
    description: str | None
    organizer_id: str
    goal_id: str
    start_time: datetime
    end_time: datetime
    google_event_id: str
    google_meet_link: str | None
    participants: list[str]
    status: MeetingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptSyncResponse(BaseModel):
    meeting_id: str
    goal_id: str
    transcript: str
    checkin_synced: bool


class MeetingsAnalyticsResponse(BaseModel):
    total_meetings: int
    completed_meetings: int
    cancelled_meetings: int
