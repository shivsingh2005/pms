from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.ai_service import AIService
from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.ai import (
    AICheckinSummarizeRequest,
    AICheckinSummarizeResponse,
    AIChatRequest,
    AIChatResponse,
    AIDecisionRequest,
    AIDecisionResponse,
    AIFeedbackCoachRequest,
    AIFeedbackCoachResponse,
    AIGoalSuggestRequest,
    AIGoalSuggestResponse,
    AIGrowthSuggestRequest,
    AIGrowthSuggestResponse,
    AIReviewGenerateRequest,
    AIReviewGenerateResponse,
    AITrainingSuggestRequest,
    AITrainingSuggestResponse,
)
from app.utils.dependencies import get_current_user

settings = get_settings()

router = APIRouter(prefix="/ai", tags=["AI"])


def _build_ai_service() -> AIService:
    service = AIService()

    async def _no_quarter_limit(user: User, db: AsyncSession) -> None:
        return

    service._enforce_quarter_limit = _no_quarter_limit  # type: ignore[method-assign]
    return service


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
