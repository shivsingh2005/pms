from datetime import datetime
from pydantic import BaseModel, Field


class LeadershipAOPCreateRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str | None = None
    total_target_value: float = Field(gt=0)
    target_unit: str = Field(min_length=1, max_length=50)
    target_metric: str = Field(min_length=2)
    year: int = Field(ge=2000, le=2200)
    quarter: int | None = Field(default=None, ge=1, le=4)
    department: str | None = Field(default=None, max_length=128)


class LeadershipAOPUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    description: str | None = None
    total_target_value: float | None = Field(default=None, gt=0)
    target_unit: str | None = Field(default=None, min_length=1, max_length=50)
    target_metric: str | None = Field(default=None, min_length=2)
    year: int | None = Field(default=None, ge=2000, le=2200)
    quarter: int | None = Field(default=None, ge=1, le=4)
    department: str | None = Field(default=None, max_length=128)
    status: str | None = None


class LeadershipAOPOut(BaseModel):
    id: str
    organization_id: str
    cycle_id: str | None = None
    title: str
    description: str | None = None
    year: int
    quarter: int | None = None
    total_target_value: float
    target_unit: str
    target_metric: str
    department: str | None = None
    status: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    assigned_target_value: float
    assigned_percentage: float
    manager_count: int


class ManagerAssignmentInput(BaseModel):
    manager_id: str
    target_value: float = Field(ge=0)
    target_percentage: float = Field(ge=0, le=100)


class AssignManagersRequest(BaseModel):
    assignments: list[ManagerAssignmentInput] = Field(default_factory=list)


class AOPManagerAssignmentOut(BaseModel):
    id: str
    aop_id: str
    manager_id: str
    manager_name: str
    manager_department: str | None = None
    assigned_target_value: float
    assigned_percentage: float
    target_unit: str | None = None
    description: str | None = None
    status: str
    acknowledged_at: datetime | None = None


class AOPProgressManagerOut(BaseModel):
    manager_id: str
    manager_name: str
    manager_department: str | None = None
    target_value: float
    achieved_value: float
    achieved_percentage: float
    status_label: str


class AOPProgressOut(BaseModel):
    aop_id: str
    title: str
    total_target_value: float
    achieved_value: float
    achieved_percentage: float
    managers: list[AOPProgressManagerOut] = Field(default_factory=list)


class CascadedManagerGoalOut(BaseModel):
    goal_id: str
    aop_id: str | None = None
    assignment_id: str | None = None
    title: str
    description: str | None = None
    target_value: float | None = None
    target_unit: str | None = None
    status: str
    assigned_by: str | None = None


class CascadeEmployeeAssignmentInput(BaseModel):
    employee_id: str
    target_value: float = Field(ge=0)
    target_percentage: float = Field(ge=0, le=100)


class CascadeToTeamRequest(BaseModel):
    employee_assignments: list[CascadeEmployeeAssignmentInput] = Field(default_factory=list)


class CascadedEmployeeGoalOut(BaseModel):
    goal_id: str
    manager_goal_id: str | None = None
    aop_id: str | None = None
    title: str
    description: str | None = None
    target_value: float | None = None
    target_unit: str | None = None
    target_percentage: float | None = None
    status: str
    contribution_level: str | None = None


class GoalLineageImpactOut(BaseModel):
    employee_goal_id: str
    employee_title: str
    employee_target_value: float | None = None
    employee_target_percentage: float | None = None
    employee_progress: float
    manager_goal_id: str | None = None
    manager_title: str | None = None
    manager_target_value: float | None = None
    manager_progress: float | None = None
    aop_id: str | None = None
    aop_title: str | None = None
    aop_total_value: float | None = None
    aop_progress: float | None = None
    contribution_level: str | None = None
    business_context: str | None = None
