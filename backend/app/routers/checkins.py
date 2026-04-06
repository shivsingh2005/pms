from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.checkin import (
    CheckinOut,
    CheckinRateRequest,
    CheckinRatingRecommendationOut,
    CheckinRatingOut,
    CheckinReviewUpdate,
    CheckinSubmit,
    CheckinSubmitResponse,
    CheckinTranscriptIngestRequest,
    CheckinTranscriptIngestResponse,
    EmployeeFinalRatingsRequest,
    EmployeeFinalRatingsResponse,
    EmployeeFinalRatingOut,
)
from app.services.checkin_service import CheckinService
from app.utils.dependencies import get_user_mode

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("", response_model=CheckinSubmitResponse)
async def create_checkin(
    payload: CheckinSubmit,
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> CheckinSubmitResponse:
    if current_user.role != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can submit check-ins")

    checkin, insights = await CheckinService.submit_checkin(current_user, payload, db)
    return CheckinSubmitResponse(checkin=CheckinOut.model_validate(checkin), insights=insights)


@router.get("", response_model=list[CheckinOut])
async def list_checkins(
    current_user: User = Depends(require_roles(UserRole.employee)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[CheckinOut]:
    if current_user.role != UserRole.employee or mode != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employee mode can access employee check-ins")

    checkins = await CheckinService.list_employee_checkins(current_user, db)
    return [CheckinOut.model_validate(item) for item in checkins]


@router.patch("/{checkin_id}", response_model=CheckinOut)
async def review_checkin(
    checkin_id: str,
    payload: CheckinReviewUpdate,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> CheckinOut:
    if current_user.role != UserRole.manager or mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only manager mode can review check-ins")

    checkin = await CheckinService.review_checkin(checkin_id, payload, current_user, db)
    return CheckinOut.model_validate(checkin)


@router.post("/{checkin_id}/rate", response_model=CheckinRatingOut)
async def rate_checkin(
    checkin_id: str,
    payload: CheckinRateRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> CheckinRatingOut:
    if current_user.role != UserRole.manager or mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only manager mode can rate check-ins")

    rating = await CheckinService.rate_checkin(checkin_id, payload, current_user, db)
    return CheckinRatingOut.model_validate(rating)


@router.get("/employee/{employee_id}/final-rating", response_model=EmployeeFinalRatingOut)
async def get_employee_final_rating(
    employee_id: str,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeFinalRatingOut:
    average_rating, ratings_count = await CheckinService.get_employee_final_rating(employee_id, current_user, db)
    return EmployeeFinalRatingOut(employee_id=employee_id, average_rating=average_rating, ratings_count=ratings_count)


@router.post("/employee/final-ratings", response_model=EmployeeFinalRatingsResponse)
async def get_employee_final_ratings_bulk(
    payload: EmployeeFinalRatingsRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeFinalRatingsResponse:
    ratings = await CheckinService.get_employee_final_ratings_bulk(
        [str(employee_id) for employee_id in payload.employee_ids],
        current_user,
        db,
    )
    items = [
        EmployeeFinalRatingOut(employee_id=employee_id, average_rating=average_rating, ratings_count=ratings_count)
        for employee_id, (average_rating, ratings_count) in ratings.items()
    ]
    return EmployeeFinalRatingsResponse(items=items)


@router.post("/{checkin_id}/transcript/ingest", response_model=CheckinTranscriptIngestResponse)
async def ingest_transcript(
    checkin_id: str,
    payload: CheckinTranscriptIngestRequest,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> CheckinTranscriptIngestResponse:
    output = await CheckinService.ingest_transcript(checkin_id, payload, current_user, db)
    return CheckinTranscriptIngestResponse(
        checkin=CheckinOut.model_validate(output["checkin"]),
        summary=output["summary"],
        key_points=output["key_points"],
        action_items=output["action_items"],
        goal_summaries=output["goal_summaries"],
    )


@router.get("/{checkin_id}/rating-recommendation", response_model=CheckinRatingRecommendationOut)
async def get_rating_recommendation(
    checkin_id: str,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> CheckinRatingRecommendationOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only manager mode can access manager rating recommendations")

    output = await CheckinService.get_rating_recommendation(checkin_id, current_user, db)
    return CheckinRatingRecommendationOut(**output)
