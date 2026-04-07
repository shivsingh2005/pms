from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import PerformanceCycleStatus
from app.models.goal import Goal
from app.models.performance_cycle import PerformanceCycle
from app.models.rating import Rating
from app.models.user import User
from app.services.cycle_guard import ensure_cycle_writable
from app.schemas.rating import RatingCreate


class RatingService:
    logger = logging.getLogger(__name__)

    @staticmethod
    async def submit(manager: User, payload: RatingCreate, db: AsyncSession) -> Rating:
        goal = await db.get(Goal, payload.goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if str(goal.user_id) != str(payload.employee_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal does not belong to employee")
        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot submit rating in a locked cycle")

        rating = Rating(
            cycle_id=goal.cycle_id,
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
        RatingService.logger.info(
            "Goal rating submitted",
            extra={
                "rating_id": str(rating.id),
                "goal_id": str(rating.goal_id),
                "employee_id": str(rating.employee_id),
                "manager_id": str(rating.manager_id),
                "cycle_id": str(rating.cycle_id) if rating.cycle_id else None,
            },
        )
        return rating

    @staticmethod
    async def list_ratings(current_user: User, db: AsyncSession) -> list[Rating]:
        if current_user.role.value in {"hr", "leadership"}:
            result = await db.execute(select(Rating))
            return list(result.scalars().all())

        result = await db.execute(
            select(Rating)
            .outerjoin(PerformanceCycle, Rating.cycle_id == PerformanceCycle.id)
            .where(
                Rating.employee_id == current_user.id,
                or_(
                    Rating.cycle_id.is_(None),
                    PerformanceCycle.status.in_([PerformanceCycleStatus.closed, PerformanceCycleStatus.locked]),
                ),
            )
            .order_by(Rating.created_at.desc())
        )
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
