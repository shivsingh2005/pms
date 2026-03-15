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


class AIChatRequest(BaseModel):
    message: str
    page: str | None = None


class AIChatResponse(BaseModel):
    response: str
    suggested_actions: list[str]
