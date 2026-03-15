from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.review import ReviewAnalyticsOut, ReviewGenerateRequest, ReviewOut
from app.services.review_service import ReviewService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["Performance Reviews"])


@router.get("", response_model=list[ReviewOut])
async def list_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewOut]:
    reviews = await ReviewService.list_reviews(current_user, db)
    return [ReviewOut.model_validate(review) for review in reviews]


@router.post("/generate", response_model=ReviewOut)
async def generate_review(
    payload: ReviewGenerateRequest,
    manager: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> ReviewOut:
    review = await ReviewService.generate_review(manager, payload, db)
    return ReviewOut.model_validate(review)


@router.get("/analytics", response_model=ReviewAnalyticsOut)
async def review_analytics(
    _: User = Depends(require_roles(UserRole.hr, UserRole.leadership, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> ReviewAnalyticsOut:
    analytics = await ReviewService.analytics(db)
    return ReviewAnalyticsOut(**analytics)
