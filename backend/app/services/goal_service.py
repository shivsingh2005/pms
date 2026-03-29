from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import GoalStatus, UserRole
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalAssignRequest, GoalCreate, GoalUpdate


class GoalService:
    @staticmethod
    def _description_with_kpi(description: str | None, kpi: str | None) -> str | None:
        base = (description or "").strip()
        kpi_text = (kpi or "").strip()
        if not kpi_text:
            return base or None
        if not base:
            return f"KPI: {kpi_text}"
        return f"{base}\n\nKPI: {kpi_text}"

    @staticmethod
    async def get_workload(user_id: UUID, db: AsyncSession) -> float:
        result = await db.execute(
            select(func.coalesce(func.sum(Goal.weightage), 0.0)).where(
                Goal.user_id == user_id,
                Goal.status != GoalStatus.rejected,
            )
        )
        return round(float(result.scalar() or 0.0), 1)

    @staticmethod
    async def create_goal(current_user: User, payload: GoalCreate, db: AsyncSession) -> Goal:
        goal = Goal(
            user_id=current_user.id,
            assigned_to=current_user.id,
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
    async def list_goals(current_user: User, mode: UserRole, db: AsyncSession) -> list[Goal]:
        stmt = select(Goal)
        if mode == UserRole.employee:
            stmt = stmt.where(Goal.user_id == current_user.id)
        elif mode == UserRole.manager:
            stmt = stmt.join(User, Goal.user_id == User.id).where(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )
        else:
            stmt = stmt.join(User, Goal.user_id == User.id).where(User.organization_id == current_user.organization_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_goal(goal_id: str, current_user: User, payload: GoalUpdate, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        changes = payload.model_dump(exclude_unset=True)

        if current_user.role == UserRole.employee:
            if goal.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
            if not changes:
                return goal
            if set(changes.keys()) != {"progress"}:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can only update progress")

        if current_user.role == UserRole.manager:
            owner = await db.get(User, goal.user_id)
            if not owner or (owner.manager_id != current_user.id and owner.id != current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can edit only direct-report goals")

        for key, value in changes.items():
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
    async def approve_goal(goal_id: str, current_user: User, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or not owner.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal owner not found")

        if current_user.role == UserRole.manager:
            if owner.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can approve only direct-report goals")
            if owner.id == current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot approve their own goals")
        elif current_user.organization_id != owner.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization approval is not allowed")

        goal.status = GoalStatus.approved
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def reject_goal(goal_id: str, current_user: User, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or not owner.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal owner not found")

        if current_user.role == UserRole.manager:
            if owner.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can reject only direct-report goals")
            if owner.id == current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot reject their own goals")
        elif current_user.organization_id != owner.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization rejection is not allowed")

        goal.status = GoalStatus.rejected
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def assign_goals(manager: User, payload: GoalAssignRequest, db: AsyncSession) -> list[Goal]:
        target_user = await db.get(User, payload.employee_id)
        if not target_user or not target_user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if manager.role == UserRole.manager and target_user.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only assign goals to direct reports")

        if manager.role != UserRole.admin and target_user.organization_id != manager.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization assignment is not allowed")

        desired_status = GoalStatus.rejected if payload.reject else GoalStatus.approved if payload.approve else GoalStatus.draft
        saved_goals: list[Goal] = []

        for item in payload.goals:
            if item.goal_id:
                goal = await db.get(Goal, item.goal_id)
                if not goal or goal.user_id != payload.employee_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found for employee")
            else:
                goal = Goal(
                    user_id=payload.employee_id,
                    assigned_to=payload.employee_id,
                    assigned_by=manager.id,
                    title=item.title,
                    description=GoalService._description_with_kpi(item.description, item.kpi),
                    weightage=item.weightage,
                    progress=item.progress,
                    framework=item.framework,
                    status=desired_status,
                    is_ai_generated=payload.is_ai_generated,
                )
                db.add(goal)
                saved_goals.append(goal)
                continue

            goal.title = item.title
            goal.description = GoalService._description_with_kpi(item.description, item.kpi)
            goal.weightage = item.weightage
            goal.framework = item.framework
            goal.progress = item.progress
            goal.status = desired_status
            goal.assigned_by = manager.id
            goal.assigned_to = payload.employee_id
            goal.is_ai_generated = payload.is_ai_generated
            saved_goals.append(goal)

        await db.commit()

        for goal in saved_goals:
            await db.refresh(goal)

        return saved_goals
