from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.performance_cycle import (
    FrameworkRecommendationResponse,
    PerformanceCycleCreate,
    PerformanceCycleOut,
    PerformanceCycleUpdate,
)
from app.services.performance_cycle_service import PerformanceCycleService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/performance-cycles", tags=["Performance Cycles"])


@router.get("", response_model=list[PerformanceCycleOut])
async def list_cycles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceCycleOut]:
    cycles = await PerformanceCycleService.list_cycles(current_user, db)
    return [PerformanceCycleOut.model_validate(cycle) for cycle in cycles]


@router.get("/active", response_model=PerformanceCycleOut | None)
async def get_active_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut | None:
    cycle = await PerformanceCycleService.get_active_cycle(current_user, db)
    if cycle is None:
        return None
    return PerformanceCycleOut.model_validate(cycle)


@router.get("/framework/recommend", response_model=FrameworkRecommendationResponse)
async def recommend_framework(
    role: str = Query(...),
    department: str | None = Query(default=None),
    _: User = Depends(get_current_user),
) -> FrameworkRecommendationResponse:
    framework, rationale = PerformanceCycleService.recommend_framework(role=role, department=department)
    return FrameworkRecommendationResponse(recommended_framework=framework, rationale=rationale)


@router.post("", response_model=PerformanceCycleOut)
async def create_cycle(
    payload: PerformanceCycleCreate,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.create_cycle(current_user, payload, db)
    return PerformanceCycleOut.model_validate(cycle)


@router.patch("/{cycle_id}", response_model=PerformanceCycleOut)
async def update_cycle(
    cycle_id: str,
    payload: PerformanceCycleUpdate,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.update_cycle(cycle_id, current_user, payload, db)
    return PerformanceCycleOut.model_validate(cycle)
