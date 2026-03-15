from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import GoalStatus, UserRole
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalService:
    @staticmethod
    async def create_goal(current_user: User, payload: GoalCreate, db: AsyncSession) -> Goal:
        goal = Goal(
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            weightage=payload.weightage,
            status=GoalStatus.draft,
            progress=payload.progress,
            framework=payload.framework,
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def list_goals(current_user: User, db: AsyncSession) -> list[Goal]:
        stmt = select(Goal)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(Goal.user_id == current_user.id)
        else:
            stmt = stmt.join(User, Goal.user_id == User.id).where(User.organization_id == current_user.organization_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_goal(goal_id: str, current_user: User, payload: GoalUpdate, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if current_user.role == UserRole.employee and goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(goal, key, value)

        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def submit_goal(goal_id: str, current_user: User, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can submit")

        goal.status = GoalStatus.submitted
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def approve_goal(goal_id: str, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        goal.status = GoalStatus.approved
        await db.commit()
        await db.refresh(goal)
        return goal
