from pydantic import BaseModel, Field


class AIGoalSuggestRequest(BaseModel):
    role: str
    department: str
    organization_objectives: str


class AIGoalItem(BaseModel):
    title: str
    description: str
    kpi: str
    weightage: float


class AIGoalSuggestResponse(BaseModel):
    goals: list[AIGoalItem]


class AIGoalGenerateRequest(BaseModel):
    user_id: str
    organization_objectives: str | None = None


class AIGoalGenerateResponse(BaseModel):
    user_id: str
    title: str
    department: str
    team_size: int
    focus_area: str
    goals: list[AIGoalItem]


class AITeamGoalGenerateRequest(BaseModel):
    manager_id: str
    organization_objectives: str | None = None


class AITeamGoalEmployeeBundle(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str
    current_workload: float
    goals: list[AIGoalItem]


class AITeamGoalGenerateResponse(BaseModel):
    manager_id: str
    team_structure: list[str]
    employees: list[AITeamGoalEmployeeBundle]


class AICheckinSummarizeRequest(BaseModel):
    meeting_transcript: str = Field(min_length=10)


class AICheckinSummarizeResponse(BaseModel):
    summary: str
    key_points: list[str]
    action_items: list[str]


class AIReviewGenerateRequest(BaseModel):
    employee_goals: list[str]
    checkin_notes: list[str]
    manager_comments: str


class AIReviewGenerateResponse(BaseModel):
    performance_summary: str
    strengths: list[str]
    weaknesses: list[str]
    growth_plan: list[str]


class AIFeedbackCoachRequest(BaseModel):
    manager_feedback: str


class AIFeedbackCoachResponse(BaseModel):
    improved_feedback: str
    tone_score: int
    suggested_version: str


class AIGrowthSuggestRequest(BaseModel):
    role: str
    department: str
    current_skills: list[str]
    target_role: str


class AIGrowthSuggestResponse(BaseModel):
    growth_suggestions: list[str]
    next_quarter_plan: list[str]
    recommended_training: list[str]


class AITrainingSuggestRequest(BaseModel):
    department: str
    skill_gaps: list[str]


class AITrainingProgram(BaseModel):
    name: str
    duration_weeks: int
    outcome: str


class AITrainingSuggestResponse(BaseModel):
    programs: list[AITrainingProgram]


class AIDecisionRequest(BaseModel):
    context: str
    questions: list[str]


class AIDecisionResponse(BaseModel):
    insights: list[str]
    risks: list[str]
    recommended_actions: list[str]


class AOPDistributionManagerContext(BaseModel):
    manager_id: str
    manager_name: str
    department: str | None = None
    team_size: int | None = None
    historical_performance: float | None = None


class AOPDistributionSuggestRequest(BaseModel):
    total_target_value: float = Field(gt=0)
    target_unit: str = Field(min_length=1, max_length=50)
    target_metric: str = Field(min_length=2)
    managers: list[AOPDistributionManagerContext] = Field(default_factory=list)


class AOPDistributionSuggestItem(BaseModel):
    manager_id: str
    manager_name: str
    suggested_value: float
    suggested_percentage: float
    rationale: str


class AOPDistributionSuggestResponse(BaseModel):
    assignments: list[AOPDistributionSuggestItem]
    distribution_rationale: str
    balance_score: int


class EmployeeCascadeSuggestContext(BaseModel):
    employee_id: str
    name: str
    role: str
    current_workload_percentage: float = Field(ge=0, le=100)
    historical_performance_score: float | None = None


class EmployeeCascadeSuggestRequest(BaseModel):
    manager_name: str
    total_target_value: float = Field(gt=0)
    target_unit: str = Field(min_length=1, max_length=50)
    target_metric: str = Field(min_length=2)
    employees: list[EmployeeCascadeSuggestContext] = Field(default_factory=list)


class EmployeeCascadeSuggestItem(BaseModel):
    employee_id: str
    suggested_value: float
    suggested_percentage: float
    rationale: str
    workload_after: float


class EmployeeCascadeSuggestResponse(BaseModel):
    assignments: list[EmployeeCascadeSuggestItem]
    total_check: float
    warnings: list[str]


class AIChatRequest(BaseModel):
    message: str
    page: str | None = None


class AIChatResponse(BaseModel):
    response: str
    suggested_actions: list[str]


class AIUsageFeatureStatus(BaseModel):
    feature_name: str
    used: int
    limit: int
    remaining: int


class AIQuarterlyUsageResponse(BaseModel):
    quarter: int
    year: int
    features: list[AIUsageFeatureStatus]


class AIRatingSuggestRequest(BaseModel):
    overall_progress: int = Field(ge=0, le=100)
    confidence_level: int = Field(default=3, ge=1, le=5)
    blockers: str | None = None
    achievements: str | None = None


class AIRatingSuggestResponse(BaseModel):
    suggested_rating: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    rationale: list[str]


# Goal Cluster Detection
class AIGoalClusterDetectRequest(BaseModel):
    goal_title: str
    goal_description: str
    goal_kpi: str
    employee_role: str
    employee_department: str
    employee_function: str


class AIGoalClusterDetectResponse(BaseModel):
    cluster_name: str
    cluster_category: str
    sub_category: str
    applicable_functions: list[str]
    goal_nature: str  # quantitative|qualitative|behavioral
    confidence: str  # High|Medium|Low
    reasoning: str


# Employee Recommendation for Goal Assignment
class AITeamMemberContext(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str | None = None
    current_workload_percentage: float = Field(ge=0, le=100)
    current_goals_count: int = 0
    historical_performance_in_similar_goals: str | None = None
    skills_demonstrated: list[str] = Field(default_factory=list)


class AIEmployeeRecommendRequest(BaseModel):
    goal_title: str
    goal_description: str
    goal_kpi: str
    goal_cluster: str
    goal_nature: str
    team_members: list[AITeamMemberContext]


class AIEmployeeRecommendation(BaseModel):
    employee_id: str
    name: str
    role: str
    match_score: float = Field(ge=0, le=100)
    match_reason: str
    current_workload: float
    workload_after_assignment: float
    fit_confidence: str  # High|Medium|Low
    risk_flag: str | None = None


class AIEmployeeNotRecommended(BaseModel):
    employee_id: str
    reason: str


class AIEmployeeRecommendResponse(BaseModel):
    recommended_employees: list[AIEmployeeRecommendation]
    not_recommended: list[AIEmployeeNotRecommended]
    cluster_insight: str


# Next Action Determination
class AINextActionRequest(BaseModel):
    cycle_status: str
    goals_count: int
    goals_submitted_count: int
    goals_approved_count: int
    checkins_count: int
    days_since_last_checkin: int
    pending_approvals: int


class AINextActionResponse(BaseModel):
    action: str  # create_goals|submit_goals|wait_approval|submit_checkin|review_pending|on_track
    message: str
    priority: str  # high|medium|low
    cta: str
    url: str | None = None
