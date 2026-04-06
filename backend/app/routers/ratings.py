from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingOut, WeightedScoreOut
from app.services.rating_service import RatingService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("", response_model=RatingOut)
async def submit_rating(
    payload: RatingCreate,
    manager: User = Depends(require_roles(UserRole.manager, UserRole.hr)),
    db: AsyncSession = Depends(get_db),
) -> RatingOut:
    rating = await RatingService.submit(manager, payload, db)
    return RatingOut.model_validate(rating)


@router.get("", response_model=list[RatingOut])
async def list_ratings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RatingOut]:
    ratings = await RatingService.list_ratings(current_user, db)
    return [RatingOut.model_validate(rating) for rating in ratings]


@router.get("/weighted-score/{employee_id}", response_model=WeightedScoreOut)
async def get_weighted_score(
    employee_id: str,
    _: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> WeightedScoreOut:
    score = await RatingService.weighted_score(employee_id, db)
    return WeightedScoreOut(employee_id=employee_id, weighted_score=score)
