from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import cache_get, cache_set
from app.models.enums import UserRole
from app.models.performance_review import PerformanceReview
from app.models.user import User
from app.schemas.review import ReviewGenerateRequest
from app.services.rating_service import RatingService


class ReviewService:
    @staticmethod
    async def list_reviews(current_user: User, db: AsyncSession) -> list[PerformanceReview]:
        stmt = select(PerformanceReview)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(PerformanceReview.employee_id == current_user.id)
        elif current_user.role == UserRole.manager:
            stmt = stmt.where(PerformanceReview.manager_id == current_user.id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def generate_review(manager: User, payload: ReviewGenerateRequest, db: AsyncSession) -> PerformanceReview:
        weighted_score = await RatingService.weighted_score(payload.employee_id, db)
        summary = f"Performance review generated with weighted score {weighted_score:.2f}"

        review = PerformanceReview(
            employee_id=payload.employee_id,
            manager_id=manager.id,
            cycle_year=payload.cycle_year,
            cycle_quarter=payload.cycle_quarter,
            overall_rating=weighted_score,
            summary=summary,
            strengths="Consistent contribution against goals",
            weaknesses="Needs improvement in low-progress goals",
            growth_areas="Strategic planning and ownership",
            created_at=datetime.now(timezone.utc),
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    @staticmethod
    async def analytics(db: AsyncSession) -> dict:
        cache_key = "reviews:analytics"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(
            select(func.count(PerformanceReview.id), func.avg(PerformanceReview.overall_rating))
        )
        total_reviews, avg_rating = result.one()
        payload = {
            "total_reviews": int(total_reviews or 0),
            "avg_rating": float(avg_rating or 0),
        }
        await cache_set(cache_key, payload)
        return payload
