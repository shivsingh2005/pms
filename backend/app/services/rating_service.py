from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.goal import Goal
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate


class RatingService:
    @staticmethod
    async def submit(manager: User, payload: RatingCreate, db: AsyncSession) -> Rating:
        rating = Rating(
            goal_id=payload.goal_id,
            manager_id=manager.id,
            employee_id=payload.employee_id,
            rating=payload.rating,
            rating_label=payload.rating_label,
            comments=payload.comments,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rating)
        await db.commit()
        await db.refresh(rating)
        return rating

    @staticmethod
    async def list_ratings(current_user: User, db: AsyncSession) -> list[Rating]:
        if current_user.role.value in {"hr", "leadership", "admin"}:
            result = await db.execute(select(Rating))
            return list(result.scalars().all())

        result = await db.execute(select(Rating).where(Rating.employee_id == current_user.id))
        return list(result.scalars().all())

    @staticmethod
    async def weighted_score(employee_id: str, db: AsyncSession) -> float:
        stmt = (
            select(func.sum(Rating.rating * Goal.weightage) / func.nullif(func.sum(Goal.weightage), 0))
            .select_from(Rating)
            .join(Goal, Goal.id == Rating.goal_id)
            .where(Rating.employee_id == employee_id)
        )
        result = await db.execute(stmt)
        score = result.scalar()
        return float(score or 0.0)
