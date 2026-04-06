from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import CheckinStatus


class GoalProgressUpdate(BaseModel):
    goal_id: UUID
    progress: int | None = Field(default=None, ge=0, le=100)
    note: str | None = None


class CheckinSubmit(BaseModel):
    overall_progress: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    achievements: str | None = None
    blockers: str | None = None
    confidence_level: int | None = Field(default=None, ge=1, le=5)
    is_final: bool = False
    goal_updates: list[GoalProgressUpdate] = Field(default_factory=list)


class CheckinReviewUpdate(BaseModel):
    manager_feedback: str
    status: CheckinStatus = CheckinStatus.reviewed


class CheckinOut(BaseModel):
    id: UUID
    cycle_id: UUID | None = None
    goal_ids: list[UUID] = Field(default_factory=list)
    goal_updates: list[GoalProgressUpdate] = Field(default_factory=list)
    employee_id: UUID
    manager_id: UUID
    overall_progress: int
    status: CheckinStatus
    summary: str
    achievements: str | None
    blockers: str | None
    confidence_level: int | None
    manager_feedback: str | None
    meeting_date: datetime | None = None
    meeting_link: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CheckinSubmitResponse(BaseModel):
    checkin: CheckinOut
    insights: list[str] = Field(default_factory=list)


class ManagerPendingCheckinOut(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str
    goal_ids: list[UUID] = Field(default_factory=list)
    goal_titles: list[str] = Field(default_factory=list)
    overall_progress: int
    summary: str | None
    achievements: str | None
    blockers: str | None
    status: CheckinStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinRateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: str | None = None


class CheckinRatingOut(BaseModel):
    id: UUID
    cycle_id: UUID | None = None
    checkin_id: UUID
    employee_id: UUID
    manager_id: UUID
    rating: int
    feedback: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeFinalRatingOut(BaseModel):
    employee_id: UUID
    average_rating: float
    ratings_count: int


class EmployeeFinalRatingsRequest(BaseModel):
    employee_ids: list[UUID] = Field(default_factory=list)


class EmployeeFinalRatingsResponse(BaseModel):
    items: list[EmployeeFinalRatingOut] = Field(default_factory=list)


class CheckinTranscriptIngestRequest(BaseModel):
    transcript: str = Field(min_length=10)


class GoalTranscriptSummary(BaseModel):
    goal_id: UUID
    goal_title: str
    summary_note: str


class CheckinTranscriptIngestResponse(BaseModel):
    checkin: CheckinOut
    summary: str
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    goal_summaries: list[GoalTranscriptSummary] = Field(default_factory=list)


class CheckinRatingRecommendationOut(BaseModel):
    checkin_id: UUID
    suggested_rating: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    rationale: list[str] = Field(default_factory=list)
    factors: dict[str, float | int | bool | None] = Field(default_factory=dict)
    override_allowed: bool = True
