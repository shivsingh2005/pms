from pydantic import BaseModel, Field
from datetime import datetime


class DashboardKPI(BaseModel):
    goals_completed: int = 0
    total_goals: int = 0
    consistency: float = 0
    review_readiness: str = "Low"
    peer_signals: int = 0
    team_goals: int = 0
    at_risk_goals: int = 0
    active_reports: int = 0
    org_health: float = 0
    cycle_completion: float = 0
    risk_flags: int = 0
    leadership_signals: int = 0


class DashboardPoint(BaseModel):
    name: str
    score: float


class DistributionPoint(BaseModel):
    name: str
    value: int


class StackRankingRow(BaseModel):
    name: str
    score: float
    trend: str


class DashboardInsights(BaseModel):
    primary: str
    secondary: str


class DashboardOverviewResponse(BaseModel):
    role: str
    kpi: DashboardKPI
    trend: list[DashboardPoint]
    velocity: list[DashboardPoint]
    distribution: list[DistributionPoint]
    heatmap: list[float]
    stack_ranking: list[StackRankingRow]
    insights: DashboardInsights


class DashboardNextActionResponse(BaseModel):
    title: str
    detail: str
    action_url: str
    action_label: str
    level: str = "info"


class EmployeeDashboardSeriesPoint(BaseModel):
    week: str
    value: float


class EmployeeDashboardDistributionPoint(BaseModel):
    name: str
    value: int


class EmployeeDashboardResponse(BaseModel):
    progress: float
    completed_goals: int
    active_goals: int
    checkins_count: int
    last_checkin: datetime | None = None
    consistency_percent: float
    manager_name: str | None = None
    manager_email: str | None = None
    manager_title: str | None = None
    review_readiness: str
    checkin_status: str
    trend: list[EmployeeDashboardSeriesPoint]
    consistency: list[EmployeeDashboardSeriesPoint]


class TimelineNode(BaseModel):
    entity_type: str
    entity_id: str
    cycle_id: str | None = None
    occurred_at: datetime
    title: str
    status: str
    metadata: dict[str, str | int | float | None] = Field(default_factory=dict)


class EmployeeTimelineResponse(BaseModel):
    items: list[TimelineNode]
