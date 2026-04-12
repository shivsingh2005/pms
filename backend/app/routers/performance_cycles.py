from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import PerformanceCycleStatus
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/performance-cycles", tags=["Performance Cycles"])


@router.get("")
async def list_performance_cycles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(PerformanceCycle)
        .where(PerformanceCycle.organization_id == current_user.organization_id)
        .order_by(PerformanceCycle.start_date.desc())
    )
    rows = list(result.scalars().all())

    return {
        "cycles": [
            {
                "id": str(row.id),
                "name": row.name,
                "description": None,
                "cycle_type": row.cycle_type,
                "framework": row.framework,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "status": row.status,
                "is_locked": row.status in {PerformanceCycleStatus.closed, PerformanceCycleStatus.locked}
                or bool(getattr(row, "locked_at", None)),
            }
            for row in rows
        ],
        "total": len(rows),
    }
