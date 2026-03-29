from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import CheckinStatus


class CheckinSubmit(BaseModel):
    goal_id: UUID
    progress: int = Field(ge=0, le=100)
    summary: str
    blockers: str | None = None
    next_steps: str | None = None


class CheckinReviewUpdate(BaseModel):
    manager_feedback: str
    status: CheckinStatus = CheckinStatus.reviewed


class CheckinOut(BaseModel):
    id: UUID
    goal_id: UUID
    employee_id: UUID
    manager_id: UUID
    progress: int
    status: CheckinStatus
    summary: str | None
    blockers: str | None
    next_steps: str | None
    manager_feedback: str | None
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
    goal_id: UUID
    goal_title: str
    progress: int
    summary: str | None
    blockers: str | None
    next_steps: str | None
    status: CheckinStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinRateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: str | None = None


class CheckinRatingOut(BaseModel):
    id: UUID
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
