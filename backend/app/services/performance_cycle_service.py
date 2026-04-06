from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.annual_operating_plan import AnnualOperatingPlan
from app.models.enums import PerformanceCycleStatus
from app.models.framework_selection import DepartmentFrameworkPolicy, UserFrameworkSelection
from app.models.kpi_library import KPILibrary
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User
from app.schemas.performance_cycle import (
    AnnualOperatingPlanCreateRequest,
    DepartmentFrameworkPolicyRequest,
    FrameworkSelectionRequest,
    KPILibraryCreateRequest,
    PerformanceCycleCreate,
    PerformanceCycleUpdate,
)


class PerformanceCycleService:
    FRAMEWORK_HINTS: dict[str, str] = {
        "engineering": "OKR",
        "sales": "MBO",
        "hr": "Competency",
        "operations": "Balanced Scorecard",
    }

    @staticmethod
    async def list_cycles(current_user: User, db: AsyncSession) -> list[PerformanceCycle]:
        result = await db.execute(
            select(PerformanceCycle)
            .where(PerformanceCycle.organization_id == current_user.organization_id)
            .order_by(PerformanceCycle.start_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_cycle(current_user: User, db: AsyncSession) -> PerformanceCycle | None:
        result = await db.execute(
            select(PerformanceCycle)
            .where(
                PerformanceCycle.organization_id == current_user.organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_cycle(current_user: User, payload: PerformanceCycleCreate, db: AsyncSession) -> PerformanceCycle:
        if payload.start_date > payload.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")

        if payload.goal_setting_deadline > payload.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="goal_setting_deadline must be within cycle")

        if payload.self_review_deadline > payload.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="self_review_deadline must be within cycle")

        if payload.is_active:
            active_cycle = await PerformanceCycleService.get_active_cycle(current_user, db)
            if active_cycle:
                active_cycle.is_active = False

        cycle = PerformanceCycle(
            organization_id=current_user.organization_id,
            name=payload.name.strip(),
            cycle_type=payload.cycle_type,
            framework=payload.framework,
            start_date=payload.start_date,
            end_date=payload.end_date,
            goal_setting_deadline=payload.goal_setting_deadline,
            self_review_deadline=payload.self_review_deadline,
            checkin_cap_per_quarter=payload.checkin_cap_per_quarter,
            ai_usage_cap_per_quarter=payload.ai_usage_cap_per_quarter,
            is_active=payload.is_active,
            status=PerformanceCycleStatus.active if payload.is_active else PerformanceCycleStatus.planning,
        )
        db.add(cycle)
        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def update_cycle(cycle_id: str, current_user: User, payload: PerformanceCycleUpdate, db: AsyncSession) -> PerformanceCycle:
        cycle = await db.get(PerformanceCycle, cycle_id)
        if not cycle or cycle.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance cycle not found")

        if cycle.status == PerformanceCycleStatus.locked:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locked cycles cannot be updated")

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("is_active") is True:
            active_cycle = await PerformanceCycleService.get_active_cycle(current_user, db)
            if active_cycle and active_cycle.id != cycle.id:
                active_cycle.is_active = False
                active_cycle.status = PerformanceCycleStatus.closed

        for key, value in update_data.items():
            setattr(cycle, key, value)

        if cycle.is_active:
            cycle.status = PerformanceCycleStatus.active
        elif cycle.status == PerformanceCycleStatus.active:
            cycle.status = PerformanceCycleStatus.closed

        if cycle.start_date > cycle.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")

        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def lock_cycle(cycle_id: str, current_user: User, db: AsyncSession) -> PerformanceCycle:
        cycle = await db.get(PerformanceCycle, cycle_id)
        if not cycle or cycle.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance cycle not found")

        if cycle.status == PerformanceCycleStatus.locked:
            return cycle

        cycle.status = PerformanceCycleStatus.locked
        cycle.locked_at = datetime.now(timezone.utc)
        cycle.is_active = False

        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def unlock_cycle(cycle_id: str, current_user: User, db: AsyncSession) -> PerformanceCycle:
        cycle = await db.get(PerformanceCycle, cycle_id)
        if not cycle or cycle.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance cycle not found")

        if cycle.status != PerformanceCycleStatus.locked and cycle.locked_at is None:
            return cycle

        cycle.locked_at = None
        cycle.status = PerformanceCycleStatus.closed

        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    def recommend_framework(role: str, department: str | None) -> tuple[str, str]:
        department_key = (department or "").strip().lower()
        role_key = role.strip().lower()

        if "sales" in role_key or department_key == "sales":
            return "MBO", "Sales roles are output-driven and MBO works well for measurable quota-style objectives."

        if "hr" in role_key or department_key in {"hr", "people", "talent"}:
            return "Competency", "HR functions benefit from competency and behavior-focused performance indicators."

        if department_key in PerformanceCycleService.FRAMEWORK_HINTS:
            fw = PerformanceCycleService.FRAMEWORK_HINTS[department_key]
            return fw, f"{department} functions generally align best with {fw} for planning and tracking."

        return "OKR", "OKR is a strong default for clarity, alignment, and periodic outcome tracking."

    @staticmethod
    async def get_framework_selection(current_user: User, db: AsyncSession) -> UserFrameworkSelection | None:
        result = await db.execute(
            select(UserFrameworkSelection).where(
                UserFrameworkSelection.user_id == current_user.id,
                UserFrameworkSelection.organization_id == current_user.organization_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save_framework_selection(
        current_user: User,
        payload: FrameworkSelectionRequest,
        db: AsyncSession,
    ) -> UserFrameworkSelection:
        existing = await PerformanceCycleService.get_framework_selection(current_user, db)
        recommendation, rationale = PerformanceCycleService.recommend_framework(
            role=current_user.role.value,
            department=current_user.department,
        )

        if existing:
            existing.selected_framework = payload.selected_framework.strip()
            existing.cycle_type = payload.cycle_type.strip().lower()
            existing.recommendation_reason = rationale if payload.selected_framework.strip().upper() == recommendation.upper() else None
            await db.commit()
            await db.refresh(existing)
            return existing

        selection = UserFrameworkSelection(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            selected_framework=payload.selected_framework.strip(),
            cycle_type=payload.cycle_type.strip().lower(),
            recommendation_reason=rationale if payload.selected_framework.strip().upper() == recommendation.upper() else None,
        )
        db.add(selection)
        await db.commit()
        await db.refresh(selection)
        return selection

    @staticmethod
    async def list_department_policies(current_user: User, db: AsyncSession) -> list[DepartmentFrameworkPolicy]:
        result = await db.execute(
            select(DepartmentFrameworkPolicy)
            .where(DepartmentFrameworkPolicy.organization_id == current_user.organization_id)
            .order_by(DepartmentFrameworkPolicy.department.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def upsert_department_policy(
        current_user: User,
        payload: DepartmentFrameworkPolicyRequest,
        db: AsyncSession,
    ) -> DepartmentFrameworkPolicy:
        department = payload.department.strip()
        if not department:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="department is required")

        normalized_frameworks = sorted({fw.strip() for fw in payload.allowed_frameworks if fw.strip()})
        if not normalized_frameworks:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="allowed_frameworks cannot be empty")

        result = await db.execute(
            select(DepartmentFrameworkPolicy).where(
                DepartmentFrameworkPolicy.organization_id == current_user.organization_id,
                DepartmentFrameworkPolicy.department == department,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.allowed_frameworks = normalized_frameworks
            existing.cycle_type = payload.cycle_type.strip().lower()
            existing.is_active = payload.is_active
            await db.commit()
            await db.refresh(existing)
            return existing

        policy = DepartmentFrameworkPolicy(
            organization_id=current_user.organization_id,
            department=department,
            allowed_frameworks=normalized_frameworks,
            cycle_type=payload.cycle_type.strip().lower(),
            is_active=payload.is_active,
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def list_kpi_library(
        current_user: User,
        db: AsyncSession,
        role: str | None = None,
        department: str | None = None,
        framework: str | None = None,
    ) -> list[KPILibrary]:
        stmt = select(KPILibrary).order_by(KPILibrary.role.asc(), KPILibrary.goal_title.asc())
        if role:
            stmt = stmt.where(KPILibrary.role == role.strip())
        if department:
            stmt = stmt.where(KPILibrary.department == department.strip())
        if framework:
            stmt = stmt.where(KPILibrary.framework == framework.strip())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_kpi_library_item(
        current_user: User,
        payload: KPILibraryCreateRequest,
        db: AsyncSession,
    ) -> KPILibrary:
        item = KPILibrary(
            role=payload.role.strip(),
            domain=payload.domain.strip() if payload.domain else None,
            department=payload.department.strip() if payload.department else None,
            goal_title=payload.goal_title.strip(),
            goal_description=payload.goal_description.strip(),
            suggested_kpi=payload.suggested_kpi.strip(),
            suggested_weight=payload.suggested_weight,
            framework=payload.framework.strip(),
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_annual_operating_plans(
        current_user: User,
        db: AsyncSession,
        year: int | None = None,
        department: str | None = None,
    ) -> list[AnnualOperatingPlan]:
        stmt = (
            select(AnnualOperatingPlan)
            .where(AnnualOperatingPlan.organization_id == current_user.organization_id)
            .order_by(AnnualOperatingPlan.year.desc(), AnnualOperatingPlan.created_at.desc())
        )
        if year is not None:
            stmt = stmt.where(AnnualOperatingPlan.year == year)
        if department:
            stmt = stmt.where(AnnualOperatingPlan.department == department.strip())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_annual_operating_plan(
        current_user: User,
        payload: AnnualOperatingPlanCreateRequest,
        db: AsyncSession,
    ) -> AnnualOperatingPlan:
        plan = AnnualOperatingPlan(
            organization_id=current_user.organization_id,
            year=payload.year,
            objective=payload.objective.strip(),
            target_value=payload.target_value.strip() if payload.target_value else None,
            department=payload.department.strip() if payload.department else None,
            created_by=current_user.id,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan
