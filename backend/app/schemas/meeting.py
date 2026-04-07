from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import MeetingProposalStatus, MeetingStatus, MeetingType


class AvailabilityResponse(BaseModel):
    available_slots: list[dict[str, str]]


class MeetingCreateRequest(BaseModel):
    title: str
    meeting_type: MeetingType = MeetingType.GENERAL
    description: str | None = None
    start_time: datetime
    end_time: datetime
    participants: list[str] = Field(default_factory=list)
    checkin_id: UUID | None = None
    goal_id: UUID | None = None
    employee_id: UUID | None = None
    manager_id: UUID | None = None


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
    checkin_id: UUID | None = None
    cycle_id: UUID | None = None
    employee_id: UUID | None = None
    manager_id: UUID | None = None
    meeting_type: MeetingType
    goal_id: UUID | None = None
    start_time: datetime
    end_time: datetime
    google_event_id: str
    meet_link: str | None = None
    google_meet_link: str | None
    participants: list[str]
    status: MeetingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptSyncResponse(BaseModel):
    meeting_id: UUID
    checkin_id: UUID | None = None
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


class MeetingProposalOut(BaseModel):
    id: UUID
    checkin_id: UUID
    employee_id: UUID
    manager_id: UUID
    proposed_start_time: datetime
    proposed_end_time: datetime
    status: MeetingProposalStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingProposalRejectRequest(BaseModel):
    suggest_new_start_time: datetime | None = None


class MeetingProposalRescheduleRequest(BaseModel):
    proposed_start_time: datetime
    proposed_end_time: datetime
