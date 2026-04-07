from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.performance_cycle import (
    DepartmentFrameworkPolicyRequest,
    DepartmentFrameworkPolicyResponse,
    FrameworkSelectionRequest,
    FrameworkSelectionResponse,
)
from app.services.performance_cycle_service import PerformanceCycleService
from app.utils.dependencies import get_current_user

router = APIRouter(tags=["Framework"])


class FrameworkSelectBody(BaseModel):
    employeeId: str | None = None
    framework: str
    cycleType: str = "quarterly"


class FrameworkRecommendOut(BaseModel):
    recommended: str
    reason: str


class HRFrameworkSettingsBody(BaseModel):
    allowedFrameworks: list[str]
    defaultFramework: str = "OKR"


@router.get("/framework/recommend", response_model=FrameworkRecommendOut)
async def recommend_framework(
    role: str,
    department: str | None = None,
    _: User = Depends(get_current_user),
) -> FrameworkRecommendOut:
    framework, rationale = PerformanceCycleService.recommend_framework(role=role, department=department)
    return FrameworkRecommendOut(recommended=framework, reason=rationale)


@router.post("/framework/select", response_model=FrameworkSelectionResponse)
async def select_framework(
    payload: FrameworkSelectBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkSelectionResponse:
    selection = await PerformanceCycleService.save_framework_selection(
        current_user,
        FrameworkSelectionRequest(selected_framework=payload.framework, cycle_type=payload.cycleType),
        db,
    )
    return FrameworkSelectionResponse(
        user_id=str(selection.user_id),
        selected_framework=selection.selected_framework,
        cycle_type=selection.cycle_type,
        recommendation_reason=selection.recommendation_reason,
    )


@router.patch("/hr/framework-settings", response_model=DepartmentFrameworkPolicyResponse)
async def update_framework_settings(
    payload: HRFrameworkSettingsBody,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> DepartmentFrameworkPolicyResponse:
    policy = await PerformanceCycleService.upsert_department_policy(
        current_user,
        DepartmentFrameworkPolicyRequest(
            department=current_user.department or "General",
            allowed_frameworks=payload.allowedFrameworks,
            cycle_type="quarterly",
            is_active=True,
        ),
        db,
    )
    return DepartmentFrameworkPolicyResponse(
        id=str(policy.id),
        department=policy.department,
        allowed_frameworks=policy.allowed_frameworks,
        cycle_type=policy.cycle_type,
        is_active=policy.is_active,
    )
