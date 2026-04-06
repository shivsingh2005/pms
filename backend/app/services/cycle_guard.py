from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PerformanceCycleStatus
from app.models.performance_cycle import PerformanceCycle


async def ensure_cycle_writable(
    db: AsyncSession,
    cycle_id,
    *,
    not_found_detail: str = "Performance cycle not found",
    locked_detail: str = "Performance cycle is locked",
) -> None:
    if cycle_id is None:
        return

    cycle = await db.get(PerformanceCycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    if cycle.status == PerformanceCycleStatus.locked or cycle.locked_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=locked_detail)
