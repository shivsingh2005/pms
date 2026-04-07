from pydantic import BaseModel


class HRManagerOption(BaseModel):
    id: str
    name: str
    email: str | None = None
    department: str | None = None
    title: str | None = None


class HREmployeePerformance(BaseModel):
    id: str
    name: str
    role: str
    department: str
    progress: float
    consistency: float
    last_checkin_status: str
    rating: int | None = None
    status: str


class HRTeamInsights(BaseModel):
    summary: list[str]


class HRHeatmapCell(BaseModel):
    employee_id: str
    employee_name: str
    progress: float
    consistency: float
    rating: float | None = None
    intensity: float
    training_need_level: str
    needs_training: bool


class HROverviewOut(BaseModel):
    total_employees: int
    total_managers: int
    at_risk_employees: int
    avg_org_performance: float
    training_heatmap: list[HRHeatmapCell]


class HREmployeeDirectoryItem(BaseModel):
    id: str
    name: str
    email: str | None = None
    role: str
    department: str
    manager_name: str | None
    manager_email: str | None = None
    progress: float
    rating: float | None
    consistency: float
    needs_training: bool


class HREmployeeProfileGoal(BaseModel):
    id: str
    title: str
    progress: float
    status: str


class HREmployeeProfileCheckin(BaseModel):
    id: str
    progress: int
    status: str
    summary: str | None
    manager_feedback: str | None
    created_at: str


class HREmployeeProfileRating(BaseModel):
    id: str
    rating: int
    rating_label: str
    comments: str | None
    created_at: str


class HREmployeeProfileOut(BaseModel):
    id: str
    name: str
    role: str
    department: str
    manager_name: str | None
    progress: float
    consistency: float
    avg_rating: float
    needs_training: bool
    ai_training_reason: str
    goals: list[HREmployeeProfileGoal]
    checkins: list[HREmployeeProfileCheckin]
    ratings: list[HREmployeeProfileRating]
    performance_trend: list[dict[str, float | str]]


class HRManagerTeamSummaryOut(BaseModel):
    manager_id: str
    manager_name: str
    team_size: int
    avg_performance: float
    consistency: float
    at_risk_employees: int
    top_performers: list[dict[str, float | str]]
    low_performers: list[dict[str, float | str]]
    workload_distribution: list[dict[str, float | str]]
    rating_distribution: list[dict[str, float | str]]
    members: list[HREmployeePerformance]


class HROrgAnalyticsOut(BaseModel):
    performance_trend: list[dict[str, float | str]]
    department_comparison: list[dict[str, float | str]]
    rating_distribution: list[dict[str, float | str]]
    checkin_consistency: list[dict[str, float | str]]


class HRCalibrationManagerOut(BaseModel):
    manager_id: str
    manager_name: str
    avg_rating: float
    org_avg_rating: float
    bias_direction: str
    delta: float


class HRCalibrationOut(BaseModel):
    managers: list[HRCalibrationManagerOut]


class HRReportResponseOut(BaseModel):
    report_type: str
    generated_at: str
    rows: list[dict]


class HRMeetingOut(BaseModel):
    id: str
    title: str
    description: str | None
    employee_id: str | None
    employee_name: str | None
    manager_id: str | None
    manager_name: str | None
    start_time: str
    end_time: str
    duration_minutes: int
    meeting_type: str
    mode: str
    notes: str | None
    participants: list[str]
    meet_link: str | None
    google_event_id: str | None
    summary: str | None
    status: str
    created_by_role: str
    created_from_checkin: bool
    rating_given: bool


class HRMeetingSummaryRequest(BaseModel):
    transcript: str


class HRMeetingSummaryOut(BaseModel):
    meeting_id: str
    summary: str


class HRNineBoxCellOut(BaseModel):
    employee_id: str
    employee_name: str
    performance_axis: str
    potential_axis: str
    box_label: str
    performance_score: float
    potential_score: float


class HRNineBoxOut(BaseModel):
    rows: list[HRNineBoxCellOut]


class HRSuccessionOut(BaseModel):
    employee_id: str
    employee_name: str
    target_role: str
    readiness_score: float
    readiness_level: str
    gaps: list[str]
    development_plan: str | None = None


