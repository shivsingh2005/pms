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
    cycle_id: UUID | None = None
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


class RoleGoalRecommendation(BaseModel):
    title: str
    description: str
    difficulty: str
    suggested_weight: float = Field(ge=0, le=100)
    kpi: str | None = None


class RoleGoalCluster(BaseModel):
    role: str
    goals: list[RoleGoalRecommendation] = Field(default_factory=list)


class GoalAssignmentRecommendationRequest(BaseModel):
    organization_objectives: str | None = None


class GoalAssignmentRecommendationResponse(BaseModel):
    manager_id: UUID
    clusters: list[RoleGoalCluster] = Field(default_factory=list)


class GoalAssignmentCandidateOut(BaseModel):
    employee_id: UUID
    employee_name: str
    role: str
    role_key: str
    goal_count: int
    total_weightage: float
    active_checkins: int
    workload_percent: float
    workload_status: str


class GoalAssignmentOneRequest(BaseModel):
    employee_id: UUID
    role: str
    title: str
    description: str | None = None
    kpi: str | None = None
    weightage: float = Field(ge=0, le=100)
    framework: GoalFramework = GoalFramework.OKR
    progress: float = Field(default=0, ge=0, le=100)
    approve: bool = False
    allow_overload: bool = False
    is_ai_generated: bool = True


class GoalAssignmentOneResponse(BaseModel):
    goal: GoalOut
    employee_workload_percent: float
    employee_workload_status: str
    warning: str | None = None


class GoalCascadeChildRequest(BaseModel):
    employee_id: UUID
    title: str
    description: str | None = None
    kpi: str | None = None
    framework: GoalFramework = GoalFramework.OKR
    weightage: float = Field(ge=0, le=100)
    progress: float = Field(default=0, ge=0, le=100)


class GoalCascadeRequest(BaseModel):
    parent_goal_id: UUID
    normalize_weights: bool = True
    children: list[GoalCascadeChildRequest] = Field(default_factory=list)


class GoalCascadeResponse(BaseModel):
    parent_goal_id: UUID
    children_created: int
    child_goal_ids: list[UUID]


class GoalLineageNodeOut(BaseModel):
    goal_id: UUID
    user_id: UUID
    title: str
    framework: GoalFramework
    weightage: float
    progress: float
    status: GoalStatus


class GoalLineageEdgeOut(BaseModel):
    parent_goal_id: UUID
    child_goal_id: UUID
    contribution_percentage: float


class GoalLineageResponse(BaseModel):
    root_goal_id: UUID
    nodes: list[GoalLineageNodeOut] = Field(default_factory=list)
    edges: list[GoalLineageEdgeOut] = Field(default_factory=list)


class GoalChangeLogOut(BaseModel):
    id: UUID
    goal_id: UUID
    changed_by: UUID | None = None
    change_type: str
    before_state: dict | None = None
    after_state: dict | None = None
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GoalDriftOut(BaseModel):
    goal_id: UUID
    user_id: UUID
    title: str
    weightage: float
    progress: float
    drift_score: float
    reason: str
