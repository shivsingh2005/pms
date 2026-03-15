from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import GoalFramework, GoalStatus


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    weightage: float = Field(ge=0, le=100)
    progress: float = Field(default=0, ge=0, le=100)
    framework: GoalFramework


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    weightage: float | None = Field(default=None, ge=0, le=100)
    progress: float | None = Field(default=None, ge=0, le=100)
    framework: GoalFramework | None = None


class GoalOut(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None
    weightage: float
    status: GoalStatus
    progress: float
    framework: GoalFramework
    created_at: datetime

    model_config = {"from_attributes": True}
