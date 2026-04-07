from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.ai_service import AIService
from app.ai.goal_cluster_service import GoalClusterAIService, NextActionAIService
from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.ai import (
    AIRatingSuggestRequest,
    AIRatingSuggestResponse,
    AICheckinSummarizeRequest,
    AICheckinSummarizeResponse,
    AIChatRequest,
    AIChatResponse,
    AIDecisionRequest,
    AIDecisionResponse,
    AOPDistributionSuggestRequest,
    AOPDistributionSuggestResponse,
    EmployeeCascadeSuggestRequest,
    EmployeeCascadeSuggestResponse,
    AIFeedbackCoachRequest,
    AIFeedbackCoachResponse,
    AIGoalSuggestRequest,
    AIGoalSuggestResponse,
    AIGoalGenerateRequest,
    AIGoalGenerateResponse,
    AIQuarterlyUsageResponse,
    AITeamGoalGenerateRequest,
    AITeamGoalGenerateResponse,
    AIGrowthSuggestRequest,
    AIGrowthSuggestResponse,
    AIReviewGenerateRequest,
    AIReviewGenerateResponse,
    AITrainingSuggestRequest,
    AITrainingSuggestResponse,
    AIGoalClusterDetectRequest,
    AIGoalClusterDetectResponse,
    AIEmployeeRecommendRequest,
    AIEmployeeRecommendResponse,
    AINextActionRequest,
    AINextActionResponse,
)
from app.utils.dependencies import get_current_user

settings = get_settings()

router = APIRouter(prefix="/ai", tags=["AI"])


def _build_ai_service() -> AIService:
    return AIService()


@router.get("/usage/quarterly", response_model=AIQuarterlyUsageResponse)
async def get_ai_quarterly_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIQuarterlyUsageResponse:
    service = _build_ai_service()
    output = await service.get_quarterly_usage(current_user, db)
    return AIQuarterlyUsageResponse(**output)


@router.post("/chat", response_model=AIChatResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def ai_chat(
    request: Request,
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    service = _build_ai_service()
    try:
        output = await service.chat(current_user, payload.message, payload.page, db)
        return AIChatResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/buddy/chat", response_model=AIChatResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def ai_buddy_chat(
    request: Request,
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    return await ai_chat(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/goals/suggest", response_model=AIGoalSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_goals(
    request: Request,
    payload: AIGoalSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGoalSuggestResponse:
    service = _build_ai_service()
    try:
        output = await service.generate_goal_suggestions(
            current_user,
            payload.role,
            payload.department,
            payload.organization_objectives,
            db,
        )
        return AIGoalSuggestResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/goals/generate", response_model=AIGoalGenerateResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def generate_goals(
    request: Request,
    payload: AIGoalGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGoalGenerateResponse:
    service = _build_ai_service()
    try:
        output = await service.generate_role_based_goals(
            requester=current_user,
            target_user_id=payload.user_id,
            organization_objectives=payload.organization_objectives,
            db=db,
        )
        return AIGoalGenerateResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/team-goals", response_model=AITeamGoalGenerateResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def generate_team_goals(
    request: Request,
    payload: AITeamGoalGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AITeamGoalGenerateResponse:
    service = _build_ai_service()
    try:
        output = await service.generate_team_goals(
            requester=current_user,
            manager_id=payload.manager_id,
            organization_objectives=payload.organization_objectives,
            db=db,
        )
        return AITeamGoalGenerateResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/checkins/summarize", response_model=AICheckinSummarizeResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def summarize_checkin(
    request: Request,
    payload: AICheckinSummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AICheckinSummarizeResponse:
    service = _build_ai_service()
    try:
        output = await service.summarize_checkin_transcript(current_user, payload.meeting_transcript, db)
        return AICheckinSummarizeResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/checkin/summarize", response_model=AICheckinSummarizeResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def summarize_checkin_alias(
    request: Request,
    payload: AICheckinSummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AICheckinSummarizeResponse:
    return await summarize_checkin(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/meeting/summarize", response_model=AICheckinSummarizeResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def summarize_meeting_alias(
    request: Request,
    payload: AICheckinSummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AICheckinSummarizeResponse:
    return await summarize_checkin(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/rating/suggest", response_model=AIRatingSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_rating(
    request: Request,
    payload: AIRatingSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIRatingSuggestResponse:
    service = _build_ai_service()
    try:
      output = await service.suggest_rating(
          current_user,
          payload.overall_progress,
          payload.confidence_level,
          payload.blockers,
          payload.achievements,
          db,
      )
      return AIRatingSuggestResponse(**output)
    except PermissionError as exc:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
      raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/review/generate", response_model=AIReviewGenerateResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def generate_review(
    request: Request,
    payload: AIReviewGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIReviewGenerateResponse:
    service = _build_ai_service()
    try:
        output = await service.generate_performance_review(
            current_user,
            payload.employee_goals,
            payload.checkin_notes,
            payload.manager_comments,
            db,
        )
        return AIReviewGenerateResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/feedback/coach", response_model=AIFeedbackCoachResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def coach_feedback(
    request: Request,
    payload: AIFeedbackCoachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIFeedbackCoachResponse:
    service = _build_ai_service()
    try:
        output = await service.generate_feedback(current_user, payload.manager_feedback, db)
        return AIFeedbackCoachResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/feedback/tone-score", response_model=AIFeedbackCoachResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def coach_feedback_alias(
    request: Request,
    payload: AIFeedbackCoachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIFeedbackCoachResponse:
    return await coach_feedback(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/growth/suggest", response_model=AIGrowthSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_growth(
    request: Request,
    payload: AIGrowthSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGrowthSuggestResponse:
    service = _build_ai_service()
    try:
        output = await service.suggest_career_growth(
            current_user,
            payload.role,
            payload.department,
            payload.current_skills,
            payload.target_role,
            db,
        )
        return AIGrowthSuggestResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/training/suggest", response_model=AITrainingSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_training(
    request: Request,
    payload: AITrainingSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AITrainingSuggestResponse:
    service = _build_ai_service()
    try:
        output = await service.suggest_training_programs(current_user, payload.department, payload.skill_gaps, db)
        return AITrainingSuggestResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/training/recommend", response_model=AITrainingSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_training_alias(
    request: Request,
    payload: AITrainingSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AITrainingSuggestResponse:
    return await suggest_training(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/decision/insights", response_model=AIDecisionResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def decision_insights(
    request: Request,
    payload: AIDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIDecisionResponse:
    service = _build_ai_service()
    try:
        output = await service.decision_intelligence(current_user, payload.context, payload.questions, db)
        return AIDecisionResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/performance/analysis", response_model=AIDecisionResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def performance_analysis_alias(
    request: Request,
    payload: AIDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIDecisionResponse:
    return await decision_insights(request=request, payload=payload, current_user=current_user, db=db)


@router.post("/aop/suggest-distribution", response_model=AOPDistributionSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_aop_distribution(
    request: Request,
    payload: AOPDistributionSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AOPDistributionSuggestResponse:
    service = _build_ai_service()
    try:
        output = await service.suggest_aop_distribution(current_user, payload, db)
        return AOPDistributionSuggestResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/goal-cascade/suggest-employee-split", response_model=EmployeeCascadeSuggestResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def suggest_employee_split(
    request: Request,
    payload: EmployeeCascadeSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeeCascadeSuggestResponse:
    service = _build_ai_service()
    try:
        output = await service.suggest_employee_split(current_user, payload, db)
        return EmployeeCascadeSuggestResponse(**output)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════
# NEW: Universal Goal Cluster Detection & Employee Recommendation
# ═══════════════════════════════════════════════════════════════


@router.post("/goals/detect-cluster", response_model=AIGoalClusterDetectResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def detect_goal_cluster(
    request: Request,
    payload: AIGoalClusterDetectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGoalClusterDetectResponse:
    """
    Detect which universal goal cluster a goal belongs to.
    Works across ALL business functions (Sales, HR, Product, Editorial, etc).
    Not limited to engineering-only categories.
    """
    service = GoalClusterAIService()
    try:
        result = await service.detect_goal_cluster(payload)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/goals/recommend-employees", response_model=AIEmployeeRecommendResponse)
@limiter.limit(settings.AI_RATE_LIMIT_DEFAULT)
async def recommend_employees_for_goal(
    request: Request,
    payload: AIEmployeeRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIEmployeeRecommendResponse:
    """
    Recommend team members most suited for a specific goal.
    Matches based on skills, goal nature, and workload capacity.
    Does NOT rely solely on job title.
    """
    service = GoalClusterAIService()
    try:
        result = await service.recommend_employees_for_goal(payload)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/users/next-action", response_model=AINextActionResponse)
async def get_next_action(
    request_body: AINextActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AINextActionResponse:
    """
    Determine the user's next action based on their performance cycle state.
    Returns a single, clear call-to-action.
    """
    service = NextActionAIService()
    result = await service.determine_next_action(request_body)
    return result
