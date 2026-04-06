from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.performance_cycle import (
    AnnualOperatingPlanCreateRequest,
    AnnualOperatingPlanResponse,
    DepartmentFrameworkPolicyRequest,
    DepartmentFrameworkPolicyResponse,
    FrameworkRecommendationResponse,
    FrameworkSelectionRequest,
    FrameworkSelectionResponse,
    KPILibraryCreateRequest,
    KPILibraryItemResponse,
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


@router.get("/framework/selection", response_model=FrameworkSelectionResponse | None)
async def get_framework_selection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkSelectionResponse | None:
    selection = await PerformanceCycleService.get_framework_selection(current_user, db)
    if selection is None:
        return None
    return FrameworkSelectionResponse(
        user_id=str(selection.user_id),
        selected_framework=selection.selected_framework,
        cycle_type=selection.cycle_type,
        recommendation_reason=selection.recommendation_reason,
    )


@router.post("/framework/selection", response_model=FrameworkSelectionResponse)
async def save_framework_selection(
    payload: FrameworkSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkSelectionResponse:
    selection = await PerformanceCycleService.save_framework_selection(current_user, payload, db)
    return FrameworkSelectionResponse(
        user_id=str(selection.user_id),
        selected_framework=selection.selected_framework,
        cycle_type=selection.cycle_type,
        recommendation_reason=selection.recommendation_reason,
    )


@router.get("/framework/policies", response_model=list[DepartmentFrameworkPolicyResponse])
async def list_framework_policies(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[DepartmentFrameworkPolicyResponse]:
    policies = await PerformanceCycleService.list_department_policies(current_user, db)
    return [
        DepartmentFrameworkPolicyResponse(
            id=str(policy.id),
            department=policy.department,
            allowed_frameworks=policy.allowed_frameworks,
            cycle_type=policy.cycle_type,
            is_active=policy.is_active,
        )
        for policy in policies
    ]


@router.post("/framework/policies", response_model=DepartmentFrameworkPolicyResponse)
async def upsert_framework_policy(
    payload: DepartmentFrameworkPolicyRequest,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> DepartmentFrameworkPolicyResponse:
    policy = await PerformanceCycleService.upsert_department_policy(current_user, payload, db)
    return DepartmentFrameworkPolicyResponse(
        id=str(policy.id),
        department=policy.department,
        allowed_frameworks=policy.allowed_frameworks,
        cycle_type=policy.cycle_type,
        is_active=policy.is_active,
    )


@router.get("/kpi-library", response_model=list[KPILibraryItemResponse])
async def list_kpi_library(
    role: str | None = Query(default=None),
    department: str | None = Query(default=None),
    framework: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KPILibraryItemResponse]:
    items = await PerformanceCycleService.list_kpi_library(
        current_user,
        db,
        role=role,
        department=department,
        framework=framework,
    )
    return [
        KPILibraryItemResponse(
            id=str(item.id),
            role=item.role,
            domain=item.domain,
            department=item.department,
            goal_title=item.goal_title,
            goal_description=item.goal_description,
            suggested_kpi=item.suggested_kpi,
            suggested_weight=item.suggested_weight,
            framework=item.framework,
        )
        for item in items
    ]


@router.post("/kpi-library", response_model=KPILibraryItemResponse)
async def create_kpi_library_item(
    payload: KPILibraryCreateRequest,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> KPILibraryItemResponse:
    item = await PerformanceCycleService.create_kpi_library_item(current_user, payload, db)
    return KPILibraryItemResponse(
        id=str(item.id),
        role=item.role,
        domain=item.domain,
        department=item.department,
        goal_title=item.goal_title,
        goal_description=item.goal_description,
        suggested_kpi=item.suggested_kpi,
        suggested_weight=item.suggested_weight,
        framework=item.framework,
    )


@router.get("/aop", response_model=list[AnnualOperatingPlanResponse])
async def list_annual_operating_plans(
    year: int | None = Query(default=None),
    department: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AnnualOperatingPlanResponse]:
    plans = await PerformanceCycleService.list_annual_operating_plans(
        current_user,
        db,
        year=year,
        department=department,
    )
    return [
        AnnualOperatingPlanResponse(
            id=str(plan.id),
            organization_id=str(plan.organization_id),
            year=plan.year,
            objective=plan.objective,
            target_value=plan.target_value,
            department=plan.department,
            created_by=str(plan.created_by) if plan.created_by else None,
        )
        for plan in plans
    ]


@router.post("/aop", response_model=AnnualOperatingPlanResponse)
async def create_annual_operating_plan(
    payload: AnnualOperatingPlanCreateRequest,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> AnnualOperatingPlanResponse:
    plan = await PerformanceCycleService.create_annual_operating_plan(current_user, payload, db)
    return AnnualOperatingPlanResponse(
        id=str(plan.id),
        organization_id=str(plan.organization_id),
        year=plan.year,
        objective=plan.objective,
        target_value=plan.target_value,
        department=plan.department,
        created_by=str(plan.created_by) if plan.created_by else None,
    )


@router.post("", response_model=PerformanceCycleOut)
async def create_cycle(
    payload: PerformanceCycleCreate,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.create_cycle(current_user, payload, db)
    return PerformanceCycleOut.model_validate(cycle)


@router.patch("/{cycle_id}", response_model=PerformanceCycleOut)
async def update_cycle(
    cycle_id: str,
    payload: PerformanceCycleUpdate,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.update_cycle(cycle_id, current_user, payload, db)
    return PerformanceCycleOut.model_validate(cycle)


@router.post("/{cycle_id}/lock", response_model=PerformanceCycleOut)
async def lock_cycle(
    cycle_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.lock_cycle(cycle_id, current_user, db)
    return PerformanceCycleOut.model_validate(cycle)


@router.post("/{cycle_id}/unlock", response_model=PerformanceCycleOut)
async def unlock_cycle(
    cycle_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> PerformanceCycleOut:
    cycle = await PerformanceCycleService.unlock_cycle(cycle_id, current_user, db)
    return PerformanceCycleOut.model_validate(cycle)
