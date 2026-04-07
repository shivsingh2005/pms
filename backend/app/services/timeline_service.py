from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_timeline import CycleTimeline
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User

DEFAULT_NODES = [
    "Goal Creation",
    "Goal Approval",
    "Check-ins",
    "Review",
    "Cycle Closed",
]


class TimelineService:
    @staticmethod
    async def get_or_create_cycle_timeline(employee: User, cycle_id: str | None, db: AsyncSession) -> dict:
        resolved_cycle_id: UUID | None = UUID(cycle_id) if cycle_id else None
        if resolved_cycle_id is None:
            cycle_result = await db.execute(
                select(PerformanceCycle)
                .where(
                    PerformanceCycle.organization_id == employee.organization_id,
                    PerformanceCycle.is_active.is_(True),
                )
                .order_by(PerformanceCycle.start_date.desc())
                .limit(1)
            )
            cycle = cycle_result.scalar_one_or_none()
            if cycle is None:
                raise ValueError("No active performance cycle found")
            resolved_cycle_id = cycle.id

        items_result = await db.execute(
            select(CycleTimeline)
            .where(
                CycleTimeline.employee_id == employee.id,
                CycleTimeline.cycle_id == resolved_cycle_id,
            )
            .order_by(CycleTimeline.created_at.asc())
        )
        items = list(items_result.scalars().all())

        if not items:
            for idx, node_name in enumerate(DEFAULT_NODES):
                status = "pending"
                if idx == 0:
                    status = "active"
                db.add(
                    CycleTimeline(
                        employee_id=employee.id,
                        cycle_id=resolved_cycle_id,
                        node_name=node_name,
                        status=status,
                    )
                )
            await db.commit()
            items_result = await db.execute(
                select(CycleTimeline)
                .where(
                    CycleTimeline.employee_id == employee.id,
                    CycleTimeline.cycle_id == resolved_cycle_id,
                )
                .order_by(CycleTimeline.created_at.asc())
            )
            items = list(items_result.scalars().all())

        return {
            "employee_id": employee.id,
            "cycle_id": resolved_cycle_id,
            "items": items,
        }
