from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from app.models.enums import PerformanceCycleStatus


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
    status: PerformanceCycleStatus
    locked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FrameworkRecommendationResponse(BaseModel):
    recommended_framework: str
    rationale: str


class FrameworkSelectionRequest(BaseModel):
    selected_framework: str = Field(min_length=2, max_length=64)
    cycle_type: str = Field(default="quarterly", min_length=3, max_length=32)


class FrameworkSelectionResponse(BaseModel):
    user_id: str
    selected_framework: str
    cycle_type: str
    recommendation_reason: str | None = None


class DepartmentFrameworkPolicyRequest(BaseModel):
    department: str = Field(min_length=1, max_length=128)
    allowed_frameworks: list[str] = Field(default_factory=list)
    cycle_type: str = Field(default="quarterly", min_length=3, max_length=32)
    is_active: bool = True


class DepartmentFrameworkPolicyResponse(BaseModel):
    id: str
    department: str
    allowed_frameworks: list[str]
    cycle_type: str
    is_active: bool


class KPILibraryCreateRequest(BaseModel):
    role: str = Field(min_length=2, max_length=128)
    domain: str | None = Field(default=None, max_length=128)
    department: str | None = Field(default=None, max_length=128)
    goal_title: str = Field(min_length=3, max_length=512)
    goal_description: str = Field(min_length=3)
    suggested_kpi: str = Field(min_length=3)
    suggested_weight: float = Field(gt=0, le=100)
    framework: str = Field(min_length=2, max_length=64)


class KPILibraryItemResponse(BaseModel):
    id: str
    role: str
    domain: str | None = None
    department: str | None = None
    goal_title: str
    goal_description: str
    suggested_kpi: str
    suggested_weight: float
    framework: str


class AnnualOperatingPlanCreateRequest(BaseModel):
    year: int = Field(ge=2000, le=2200)
    objective: str = Field(min_length=3)
    target_value: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=128)


class AnnualOperatingPlanResponse(BaseModel):
    id: str
    organization_id: str
    year: int
    objective: str
    target_value: str | None = None
    department: str | None = None
    created_by: str | None = None
