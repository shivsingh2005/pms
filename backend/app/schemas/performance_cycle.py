from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


ALLOWED_CYCLE_TYPES = {"quarterly", "yearly", "hybrid"}
ALLOWED_FRAMEWORKS = {"OKR", "MBO", "Hybrid", "Balanced Scorecard", "Competency", "Custom"}


class PerformanceCycleCreate(BaseModel):
    name: str
    cycle_type: str
    framework: str
    start_date: date
    end_date: date
    goal_setting_deadline: date
    self_review_deadline: date
    checkin_cap_per_quarter: int = Field(default=5, ge=1, le=20)
    ai_usage_cap_per_quarter: int = Field(default=3, ge=1, le=20)
    is_active: bool = False

    @field_validator("cycle_type")
    @classmethod
    def validate_cycle_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CYCLE_TYPES:
            raise ValueError("cycle_type must be quarterly, yearly, or hybrid")
        return normalized

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in ALLOWED_FRAMEWORKS:
            raise ValueError("Unsupported framework")
        return normalized


class PerformanceCycleUpdate(BaseModel):
    name: str | None = None
    cycle_type: str | None = None
    framework: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    goal_setting_deadline: date | None = None
    self_review_deadline: date | None = None
    checkin_cap_per_quarter: int | None = Field(default=None, ge=1, le=20)
    ai_usage_cap_per_quarter: int | None = Field(default=None, ge=1, le=20)
    is_active: bool | None = None

    @field_validator("cycle_type")
    @classmethod
    def validate_cycle_type(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CYCLE_TYPES:
            raise ValueError("cycle_type must be quarterly, yearly, or hybrid")
        return normalized

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if normalized not in ALLOWED_FRAMEWORKS:
            raise ValueError("Unsupported framework")
        return normalized


class PerformanceCycleOut(BaseModel):
    id: str
    organization_id: str
    name: str
    cycle_type: str
    framework: str
    start_date: date
    end_date: date
    goal_setting_deadline: date
    self_review_deadline: date
    checkin_cap_per_quarter: int
    ai_usage_cap_per_quarter: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FrameworkRecommendationResponse(BaseModel):
    recommended_framework: str
    rationale: str
