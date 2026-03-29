from datetime import datetime
from pydantic import BaseModel


class ManagerTeamMember(BaseModel):
    id: str
    name: str
    role: str
    department: str
    profile_avatar: str | None = None
    goal_progress_percent: float
    status: str
    current_workload: float
    current_goals_count: int
    consistency_percent: float = 0
    avg_final_rating: float = 0


class ManagerGoalHistoryItem(BaseModel):
    id: str
    title: str
    progress: float
    status: str


class ManagerCheckinItem(BaseModel):
    id: str
    meeting_date: datetime
    summary: str | None = None
    notes: str | None = None


class ManagerRatingItem(BaseModel):
    id: str
    rating: str
    comments: str | None = None
    created_at: datetime


class ManagerPerformanceItem(BaseModel):
    cycle_year: int
    cycle_quarter: int
    overall_rating: float | None = None
    summary: str | None = None
    comments: str | None = None


class ManagerAIInsights(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    growth_areas: list[str]


class ManagerEmployeeInspectionResponse(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    email: str
    progress: float
    goals_completed: int
    consistency: float
    last_checkin: datetime | None = None

    goals: list[ManagerGoalHistoryItem]
    checkins: list[ManagerCheckinItem]
    ratings: list[ManagerRatingItem]
    ai_insights: ManagerAIInsights

    # Backward-compatible fields still used in legacy manager views.
    employee_name: str | None = None
    current_workload: float
    performance_history: list[ManagerPerformanceItem]


class ManagerTeamPerformanceTrendPoint(BaseModel):
    week: str
    progress: float


class ManagerTeamPerformanceDistributionItem(BaseModel):
    label: str
    count: int


class ManagerTeamPerformanceWorkloadItem(BaseModel):
    employee_id: str
    employee_name: str
    total_weightage: float


class ManagerTeamPerformancePerformerItem(BaseModel):
    employee_id: str
    employee_name: str
    progress: float


class ManagerTeamPerformancePerformers(BaseModel):
    top: list[ManagerTeamPerformancePerformerItem]
    low: list[ManagerTeamPerformancePerformerItem]


class ManagerTeamPerformanceResponse(BaseModel):
    avg_progress: float
    completed_goals: int
    consistency: float
    at_risk: int
    trend: list[ManagerTeamPerformanceTrendPoint]
    distribution: list[ManagerTeamPerformanceDistributionItem]
    workload: list[ManagerTeamPerformanceWorkloadItem]
    performers: ManagerTeamPerformancePerformers
    insights: list[str]
