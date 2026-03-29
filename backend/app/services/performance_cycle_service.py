from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User
from app.schemas.performance_cycle import PerformanceCycleCreate, PerformanceCycleUpdate


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

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("is_active") is True:
            active_cycle = await PerformanceCycleService.get_active_cycle(current_user, db)
            if active_cycle and active_cycle.id != cycle.id:
                active_cycle.is_active = False

        for key, value in update_data.items():
            setattr(cycle, key, value)

        if cycle.start_date > cycle.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")

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
