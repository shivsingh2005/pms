from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ReviewGenerateRequest(BaseModel):
    employee_id: UUID
    cycle_year: int = Field(ge=2000, le=2100)
    cycle_quarter: int = Field(ge=1, le=4)


class ReviewOut(BaseModel):
    id: UUID
    employee_id: UUID
    manager_id: UUID
    cycle_year: int
    cycle_quarter: int
    overall_rating: float | None
    summary: str | None
    strengths: str | None
    weaknesses: str | None
    growth_areas: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAnalyticsOut(BaseModel):
    total_reviews: int
    avg_rating: float


class ReviewNarrativeRequest(BaseModel):
    period: str = Field(default="quarter", pattern="^(quarter|year)$")
    cycle_year: int | None = Field(default=None, ge=2000, le=2100)
    cycle_quarter: int | None = Field(default=None, ge=1, le=4)
    manager_comments: str = Field(default="")


class ReviewNarrativeExplainabilityOut(BaseModel):
    scope: str
    review_count: int
    source_review_ids: list[UUID]
    filters: dict[str, int | str | None]


class ReviewNarrativeOut(BaseModel):
    period: str
    cycle_year: int | None
    cycle_quarter: int | None
    performance_summary: str
    strengths: list[str]
    weaknesses: list[str]
    growth_plan: list[str]
    explainability: ReviewNarrativeExplainabilityOut
