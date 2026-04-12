from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
async def list_employees(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
            User.role == UserRole.employee,
            User.is_active.is_(True),
        )
        .order_by(User.name.asc())
        .offset(offset)
        .limit(limit)
    )
    rows = list(result.scalars().all())

    return {
        "employees": [
            {
                "id": str(row.id),
                "name": row.name,
                "email": row.email,
                "department": row.department,
                "title": row.title,
                "manager_id": str(row.manager_id) if row.manager_id else None,
            }
            for row in rows
        ],
        "total": len(rows),
    }
