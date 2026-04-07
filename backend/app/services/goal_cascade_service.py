from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annual_operating_plan import AnnualOperatingPlan
from app.models.aop_manager_assignment import AOPManagerAssignment
from app.models.enums import GoalFramework, GoalStatus, UserRole
from app.models.goal import Goal, GoalLineage
from app.models.user import User
from app.schemas.goal_cascade import (
    AssignManagersRequest,
    CascadeToTeamRequest,
    LeadershipAOPCreateRequest,
    LeadershipAOPUpdateRequest,
)


class GoalCascadeService:
    @staticmethod
    def _as_float(value: Decimal | float | int | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _compute_contribution_level(percentage: float) -> str:
        if percentage >= 25:
            return "High"
        if percentage >= 10:
            return "Medium"
        return "Low"

    @staticmethod
    async def list_aop(current_user: User, db: AsyncSession) -> list[dict]:
        rows = await db.execute(
            select(AnnualOperatingPlan)
            .where(AnnualOperatingPlan.organization_id == current_user.organization_id)
            .order_by(AnnualOperatingPlan.year.desc(), AnnualOperatingPlan.quarter.desc().nullslast(), AnnualOperatingPlan.created_at.desc())
        )
        plans = list(rows.scalars().all())

        result: list[dict] = []
        for plan in plans:
            assignment_row = await db.execute(
                select(
                    func.coalesce(func.sum(AOPManagerAssignment.assigned_target_value), 0.0),
                    func.coalesce(func.count(AOPManagerAssignment.id), 0),
                ).where(AOPManagerAssignment.aop_id == plan.id)
            )
            assigned_value, manager_count = assignment_row.one()
            total = GoalCascadeService._as_float(plan.total_target_value)
            assigned = GoalCascadeService._as_float(assigned_value)
            percentage = round((assigned * 100.0 / total), 1) if total > 0 else 0.0
            result.append(
                {
                    "id": str(plan.id),
                    "organization_id": str(plan.organization_id),
                    "cycle_id": str(plan.cycle_id) if plan.cycle_id else None,
                    "title": (plan.title or plan.objective or "AOP Target"),
                    "description": plan.description,
                    "year": plan.year,
                    "quarter": plan.quarter,
                    "total_target_value": total,
                    "target_unit": plan.target_unit or "units",
                    "target_metric": plan.target_metric or "business outcome",
                    "department": plan.department,
                    "status": plan.status,
                    "created_by": str(plan.created_by) if plan.created_by else None,
                    "created_at": plan.created_at,
                    "updated_at": plan.updated_at,
                    "assigned_target_value": assigned,
                    "assigned_percentage": percentage,
                    "manager_count": int(manager_count or 0),
                }
            )
        return result

    @staticmethod
    async def create_aop(current_user: User, payload: LeadershipAOPCreateRequest, db: AsyncSession) -> AnnualOperatingPlan:
        plan = AnnualOperatingPlan(
            organization_id=current_user.organization_id,
            title=payload.title.strip(),
            description=(payload.description or "").strip() or None,
            objective=(payload.description or payload.title).strip(),
            year=payload.year,
            quarter=payload.quarter,
            total_target_value=payload.total_target_value,
            target_unit=payload.target_unit.strip(),
            target_metric=payload.target_metric.strip(),
            target_value=f"{payload.total_target_value} {payload.target_unit.strip()}",
            department=(payload.department or "").strip() or None,
            status="active",
            created_by=current_user.id,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def update_aop(aop_id: str, current_user: User, payload: LeadershipAOPUpdateRequest, db: AsyncSession) -> AnnualOperatingPlan:
        plan = await db.get(AnnualOperatingPlan, aop_id)
        if not plan or plan.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AOP target not found")

        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(plan, key, value)

        if plan.title and not plan.objective:
            plan.objective = plan.title
        if plan.total_target_value and plan.target_unit:
            plan.target_value = f"{GoalCascadeService._as_float(plan.total_target_value)} {plan.target_unit}"

        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def list_aop_assignments(aop_id: str, current_user: User, db: AsyncSession) -> list[dict]:
        plan = await db.get(AnnualOperatingPlan, aop_id)
        if not plan or plan.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AOP target not found")

        rows = await db.execute(
            select(AOPManagerAssignment, User)
            .join(User, User.id == AOPManagerAssignment.manager_id)
            .where(AOPManagerAssignment.aop_id == plan.id)
            .order_by(User.name.asc())
        )

        items: list[dict] = []
        for assignment, manager in rows.all():
            items.append(
                {
                    "id": str(assignment.id),
                    "aop_id": str(assignment.aop_id),
                    "manager_id": str(assignment.manager_id),
                    "manager_name": manager.name,
                    "manager_department": manager.department,
                    "assigned_target_value": GoalCascadeService._as_float(assignment.assigned_target_value),
                    "assigned_percentage": float(assignment.assigned_percentage),
                    "target_unit": assignment.target_unit,
                    "description": assignment.description,
                    "status": assignment.status,
                    "acknowledged_at": assignment.acknowledged_at,
                }
            )
        return items

    @staticmethod
    async def assign_managers(aop_id: str, current_user: User, payload: AssignManagersRequest, db: AsyncSession) -> list[dict]:
        plan = await db.get(AnnualOperatingPlan, aop_id)
        if not plan or plan.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AOP target not found")

        total_percentage = round(sum(item.target_percentage for item in payload.assignments), 2)
        if total_percentage > 100.0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total assignment percentage cannot exceed 100")

        await db.execute(
            AOPManagerAssignment.__table__.delete().where(AOPManagerAssignment.aop_id == plan.id)
        )

        created: list[AOPManagerAssignment] = []
        for item in payload.assignments:
            manager = await db.get(User, item.manager_id)
            if not manager or manager.organization_id != current_user.organization_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Manager not found: {item.manager_id}")
            if manager.role != UserRole.manager:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User is not a manager: {manager.name}")

            assignment = AOPManagerAssignment(
                aop_id=plan.id,
                manager_id=manager.id,
                assigned_target_value=item.target_value,
                assigned_percentage=item.target_percentage,
                target_unit=plan.target_unit,
                description=plan.description,
                status="pending",
                created_by=current_user.id,
            )
            db.add(assignment)
            await db.flush()
            created.append(assignment)

            manager_goal = Goal(
                cycle_id=plan.cycle_id,
                user_id=manager.id,
                assigned_by=current_user.id,
                assigned_to=manager.id,
                title=f"{plan.title or 'AOP Target'}: {item.target_value} {plan.target_unit or ''}".strip(),
                description=plan.description or plan.objective,
                weightage=item.target_percentage,
                status=GoalStatus.approved,
                progress=0.0,
                framework=GoalFramework.OKR,
                aop_id=plan.id,
                aop_assignment_id=assignment.id,
                is_cascaded_from_leadership=True,
                leadership_target_value=item.target_value,
                leadership_target_unit=plan.target_unit,
                cascade_source="leadership",
            )
            db.add(manager_goal)

        await db.commit()
        return await GoalCascadeService.list_aop_assignments(aop_id, current_user, db)

    @staticmethod
    async def aop_progress(aop_id: str, current_user: User, db: AsyncSession) -> dict:
        plan = await db.get(AnnualOperatingPlan, aop_id)
        if not plan or plan.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AOP target not found")

        assignments = await GoalCascadeService.list_aop_assignments(aop_id, current_user, db)

        manager_rows: list[dict] = []
        achieved_total = 0.0
        for assignment in assignments:
            manager_goal_row = await db.execute(
                select(Goal)
                .where(
                    Goal.aop_id == plan.id,
                    Goal.aop_assignment_id == UUID(assignment["id"]),
                    Goal.user_id == UUID(assignment["manager_id"]),
                )
                .order_by(Goal.created_at.desc())
                .limit(1)
            )
            manager_goal = manager_goal_row.scalar_one_or_none()
            progress = GoalCascadeService._as_float(manager_goal.progress if manager_goal else 0.0)
            achieved_value = round(assignment["assigned_target_value"] * progress / 100.0, 2)
            achieved_total += achieved_value

            status_label = "On Track"
            if progress < 30:
                status_label = "At Risk"
            elif progress >= 60:
                status_label = "Ahead"

            manager_rows.append(
                {
                    "manager_id": assignment["manager_id"],
                    "manager_name": assignment["manager_name"],
                    "manager_department": assignment["manager_department"],
                    "target_value": assignment["assigned_target_value"],
                    "achieved_value": achieved_value,
                    "achieved_percentage": round(progress, 1),
                    "status_label": status_label,
                }
            )

        total_target = GoalCascadeService._as_float(plan.total_target_value)
        achieved_percentage = round((achieved_total * 100.0 / total_target), 1) if total_target > 0 else 0.0

        return {
            "aop_id": str(plan.id),
            "title": plan.title or plan.objective,
            "total_target_value": total_target,
            "achieved_value": round(achieved_total, 2),
            "achieved_percentage": achieved_percentage,
            "managers": manager_rows,
        }

    @staticmethod
    async def manager_cascaded_goals(current_user: User, db: AsyncSession) -> list[dict]:
        rows = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == current_user.id,
                Goal.aop_id.is_not(None),
                Goal.cascade_source == "leadership",
            )
            .order_by(Goal.created_at.desc())
        )
        goals = list(rows.scalars().all())
        return [
            {
                "goal_id": str(goal.id),
                "aop_id": str(goal.aop_id) if goal.aop_id else None,
                "assignment_id": str(goal.aop_assignment_id) if goal.aop_assignment_id else None,
                "title": goal.title,
                "description": goal.description,
                "target_value": GoalCascadeService._as_float(goal.leadership_target_value),
                "target_unit": goal.leadership_target_unit,
                "status": goal.status.value,
                "assigned_by": str(goal.assigned_by) if goal.assigned_by else None,
            }
            for goal in goals
        ]

    @staticmethod
    async def manager_acknowledge(goal_id: str, current_user: User, db: AsyncSession) -> dict:
        goal = await db.get(Goal, goal_id)
        if not goal or goal.user_id != current_user.id or goal.cascade_source != "leadership":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cascaded goal not found")

        if goal.aop_assignment_id:
            assignment = await db.get(AOPManagerAssignment, goal.aop_assignment_id)
            if assignment:
                assignment.status = "acknowledged"
                assignment.acknowledged_at = datetime.now(timezone.utc)

        await db.commit()
        return {"acknowledged": True, "goal_id": str(goal.id)}

    @staticmethod
    async def manager_cascade_to_team(goal_id: str, current_user: User, payload: CascadeToTeamRequest, db: AsyncSession) -> dict:
        manager_goal = await db.get(Goal, goal_id)
        if not manager_goal or manager_goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager cascaded goal not found")

        total_percentage = round(sum(item.target_percentage for item in payload.employee_assignments), 2)
        if total_percentage > 100.0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee assignment percentage cannot exceed 100")

        created_ids: list[str] = []
        for item in payload.employee_assignments:
            employee = await db.get(User, item.employee_id)
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee not found in your team: {item.employee_id}")

            employee_goal = Goal(
                cycle_id=manager_goal.cycle_id,
                user_id=employee.id,
                assigned_by=current_user.id,
                assigned_to=employee.id,
                title=f"{manager_goal.title} · Contribution {item.target_value} {manager_goal.leadership_target_unit or ''}".strip(),
                description=manager_goal.description,
                weightage=item.target_percentage,
                status=GoalStatus.approved,
                progress=0.0,
                framework=manager_goal.framework,
                aop_id=manager_goal.aop_id,
                aop_assignment_id=manager_goal.aop_assignment_id,
                is_cascaded_from_leadership=True,
                leadership_target_value=item.target_value,
                leadership_target_unit=manager_goal.leadership_target_unit,
                cascade_source="manager",
            )
            db.add(employee_goal)
            await db.flush()

            contribution_level = GoalCascadeService._compute_contribution_level(item.target_percentage)
            lineage = GoalLineage(
                parent_goal_id=manager_goal.id,
                child_goal_id=employee_goal.id,
                contribution_percentage=item.target_percentage,
                created_by=current_user.id,
                employee_goal_id=employee_goal.id,
                manager_goal_id=manager_goal.id,
                aop_id=manager_goal.aop_id,
                aop_assignment_id=manager_goal.aop_assignment_id,
                employee_target_value=item.target_value,
                employee_target_percentage=item.target_percentage,
                manager_target_value=GoalCascadeService._as_float(manager_goal.leadership_target_value),
                aop_total_value=GoalCascadeService._as_float((await db.get(AnnualOperatingPlan, manager_goal.aop_id)).total_target_value if manager_goal.aop_id else None),
                contribution_level=contribution_level,
                business_context=(
                    f"{item.target_value} {manager_goal.leadership_target_unit or ''} of manager target "
                    f"{GoalCascadeService._as_float(manager_goal.leadership_target_value)} {manager_goal.leadership_target_unit or ''}"
                ).strip(),
            )
            db.add(lineage)
            created_ids.append(str(employee_goal.id))

        await db.commit()
        return {"created_goals": created_ids, "count": len(created_ids)}

    @staticmethod
    async def employee_cascaded_goals(current_user: User, db: AsyncSession) -> list[dict]:
        rows = await db.execute(
            select(Goal, GoalLineage)
            .outerjoin(GoalLineage, and_(GoalLineage.employee_goal_id == Goal.id, GoalLineage.child_goal_id == Goal.id))
            .where(
                Goal.user_id == current_user.id,
                Goal.cascade_source == "manager",
            )
            .order_by(Goal.created_at.desc())
        )

        out: list[dict] = []
        for goal, lineage in rows.all():
            out.append(
                {
                    "goal_id": str(goal.id),
                    "manager_goal_id": str(lineage.manager_goal_id) if lineage and lineage.manager_goal_id else None,
                    "aop_id": str(goal.aop_id) if goal.aop_id else None,
                    "title": goal.title,
                    "description": goal.description,
                    "target_value": GoalCascadeService._as_float(goal.leadership_target_value),
                    "target_unit": goal.leadership_target_unit,
                    "target_percentage": float(lineage.employee_target_percentage) if lineage and lineage.employee_target_percentage is not None else None,
                    "status": goal.status.value,
                    "contribution_level": lineage.contribution_level if lineage else None,
                }
            )
        return out

    @staticmethod
    async def employee_acknowledge(goal_id: str, current_user: User, db: AsyncSession) -> dict:
        goal = await db.get(Goal, goal_id)
        if not goal or goal.user_id != current_user.id or goal.cascade_source != "manager":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cascaded employee goal not found")
        return {"acknowledged": True, "goal_id": str(goal.id)}

    @staticmethod
    async def employee_goal_lineage(goal_id: str, current_user: User, db: AsyncSession) -> dict:
        goal = await db.get(Goal, goal_id)
        if not goal or goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        lineage_row = await db.execute(
            select(GoalLineage)
            .where(GoalLineage.employee_goal_id == goal.id)
            .order_by(GoalLineage.created_at.desc())
            .limit(1)
        )
        lineage = lineage_row.scalar_one_or_none()

        manager_goal = await db.get(Goal, lineage.manager_goal_id) if lineage and lineage.manager_goal_id else None
        aop = await db.get(AnnualOperatingPlan, lineage.aop_id) if lineage and lineage.aop_id else None

        manager_progress = GoalCascadeService._as_float(manager_goal.progress if manager_goal else 0.0)
        manager_achieved = GoalCascadeService._as_float(lineage.manager_target_value if lineage else 0.0) * manager_progress / 100.0

        aop_total = GoalCascadeService._as_float(aop.total_target_value if aop else 0.0)
        aop_progress = round((manager_achieved * 100.0 / aop_total), 1) if aop_total > 0 else 0.0

        return {
            "employee_goal_id": str(goal.id),
            "employee_title": goal.title,
            "employee_target_value": GoalCascadeService._as_float(goal.leadership_target_value),
            "employee_target_percentage": float(lineage.employee_target_percentage) if lineage and lineage.employee_target_percentage is not None else None,
            "employee_progress": GoalCascadeService._as_float(goal.progress),
            "manager_goal_id": str(manager_goal.id) if manager_goal else None,
            "manager_title": manager_goal.title if manager_goal else None,
            "manager_target_value": GoalCascadeService._as_float(lineage.manager_target_value if lineage else 0.0),
            "manager_progress": manager_progress if manager_goal else None,
            "aop_id": str(aop.id) if aop else None,
            "aop_title": (aop.title or aop.objective) if aop else None,
            "aop_total_value": aop_total if aop else None,
            "aop_progress": aop_progress if aop else None,
            "contribution_level": lineage.contribution_level if lineage else None,
            "business_context": lineage.business_context if lineage else None,
        }
