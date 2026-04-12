from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.framework_selection import DepartmentFrameworkPolicy, UserFrameworkSelection
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/framework", tags=["Framework"])


@router.get("")
async def list_frameworks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_selection_result = await db.execute(
        select(UserFrameworkSelection).where(UserFrameworkSelection.user_id == current_user.id)
    )
    user_rows = list(user_selection_result.scalars().all())

    policies_result = await db.execute(
        select(DepartmentFrameworkPolicy).where(
            DepartmentFrameworkPolicy.organization_id == current_user.organization_id
        )
    )
    policy_rows = list(policies_result.scalars().all())

    return {
        "frameworks": {
            "user_selections": [
                {
                    "id": str(row.id),
                    "cycle_id": str(row.cycle_id),
                    "framework_type": row.framework_type,
                    "is_selected": row.is_selected,
                }
                for row in user_rows
            ],
            "department_policies": [
                {
                    "id": str(row.id),
                    "cycle_id": str(row.cycle_id),
                    "department": row.department,
                    "framework_type": row.framework_type,
                    "is_mandatory": row.is_mandatory,
                }
                for row in policy_rows
            ],
        },
        "total": len(user_rows) + len(policy_rows),
    }
