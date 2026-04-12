"""Cycle guard service for managing performance cycle write access."""

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import PerformanceCycleStatus
from app.models.performance_cycle import PerformanceCycle


async def ensure_cycle_writable(db: AsyncSession, cycle_id: str | UUID | None, locked_detail: str = "Cycle is locked") -> PerformanceCycle | None:
    """Ensure that a performance cycle is writable (not locked).
    
    Args:
        db: Database session
        cycle_id: The ID of the cycle to check
        locked_detail: Custom error message for locked cycles
        
    Returns:
        The cycle object if it exists and is writable, or None if cycle_id is None
        
    Raises:
        HTTPException: If the cycle is locked or does not exist
    """
    if cycle_id is None:
        return None
    
    result = await db.execute(select(PerformanceCycle).where(PerformanceCycle.id == cycle_id))
    cycle = result.scalar_one_or_none()
    
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance cycle not found"
        )
    
    if cycle.status in {PerformanceCycleStatus.closed, PerformanceCycleStatus.locked} or getattr(cycle, "locked_at", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=locked_detail
        )
    
    return cycle
