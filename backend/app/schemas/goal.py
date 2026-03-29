from datetime import datetime
from uuid import UUID
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
    id: UUID
    user_id: UUID
    assigned_by: UUID | None = None
    assigned_to: UUID | None = None
    title: str
    description: str | None
    weightage: float
    status: GoalStatus
    progress: float
    framework: GoalFramework
    is_ai_generated: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class GoalAssignItem(BaseModel):
    goal_id: UUID | None = None
    title: str
    description: str | None = None
    kpi: str | None = None
    weightage: float = Field(ge=0, le=100)
    framework: GoalFramework = GoalFramework.OKR
    progress: float = Field(default=0, ge=0, le=100)


class GoalAssignRequest(BaseModel):
    employee_id: UUID
    approve: bool = False
    reject: bool = False
    is_ai_generated: bool = True
    goals: list[GoalAssignItem] = Field(default_factory=list)
