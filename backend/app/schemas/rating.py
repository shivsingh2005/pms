from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import RatingLabel


class RatingCreate(BaseModel):
    goal_id: str
    employee_id: str
    rating: int = Field(ge=1, le=5)
    rating_label: RatingLabel
    comments: str | None = None


class RatingOut(BaseModel):
    id: str
    cycle_id: str | None = None
    goal_id: str
    manager_id: str
    employee_id: str
    rating: int
    rating_label: RatingLabel
    comments: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WeightedScoreOut(BaseModel):
    employee_id: str
    weighted_score: float
