from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.manager_service import ManagerService
from app.utils.dependencies import get_user_mode

router = APIRouter(prefix="/manager", tags=["Manager"])


@router.get("/team")
async def get_manager_team(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view team")
    return await ManagerService.list_team(current_user, db)


@router.get("/dashboard")
async def get_manager_dashboard(
    managerId: UUID | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view dashboard")

    resolved_manager_id = managerId or current_user.id
    if current_user.id != resolved_manager_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager ID mismatch")

    return await ManagerService.get_dashboard_payload(current_user, db)


@router.get("/team-performance")
async def get_manager_team_performance(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view team performance")

    return await ManagerService.get_team_performance_payload(current_user, db)


@router.get("/stack-ranking")
async def get_manager_stack_ranking(
    sort_by: Literal["progress", "rating", "consistency"] = Query(default="progress"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    at_risk_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view stack ranking")

    return await ManagerService.get_stack_ranking_payload(
        current_user,
        db,
        sort_by=sort_by,
        order=order,
        at_risk_only=at_risk_only,
        limit=limit,
    )


@router.get("/employee/{employee_id}")
async def get_manager_employee_inspection(
    employee_id: UUID,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view employee profile")

    payload = await ManagerService.inspect_employee(current_user, employee_id, db)
    if not payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found in your team")
    return payload
