from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogOut,
    AdminBulkUploadRequest,
    AdminBulkUploadResult,
    AdminDashboardOut,
    AdminOrgStructureOut,
    AdminRolePermissionOut,
    AdminRolePermissionsUpdate,
    AdminRolePermissionUpsert,
    AdminSystemSettingsOut,
    AdminSystemSettingsUpdate,
    AdminUserCreate,
    AdminUserOut,
    AdminUsersListOut,
    AdminUserUpdate,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
async def get_admin_dashboard(
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardOut:
    payload = await AdminService.get_dashboard(current_user, db)
    return AdminDashboardOut(**payload)


@router.get("/users", response_model=AdminUsersListOut)
async def list_admin_users(
    role: str | None = Query(default=None),
    manager_id: str | None = Query(default=None),
    department: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, pattern="^(active|inactive)$"),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminUsersListOut:
    payload = await AdminService.list_users(
        current_user=current_user,
        db=db,
        role=role,
        manager_id=manager_id,
        department=department,
        status_filter=status_filter,
        search=search,
    )
    return AdminUsersListOut(**payload)


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    payload: AdminUserCreate,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    created = await AdminService.create_user(current_user, payload, db)
    return AdminUserOut(**created)


@router.put("/users/{user_id}", response_model=AdminUserOut)
async def update_admin_user(
    user_id: str,
    payload: AdminUserUpdate,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    updated = await AdminService.update_user(current_user, user_id, payload, db)
    return AdminUserOut(**updated)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.soft_delete_user(current_user, user_id, db)


@router.post("/users/bulk-upload", response_model=AdminBulkUploadResult)
async def bulk_upload_users(
    payload: AdminBulkUploadRequest,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminBulkUploadResult:
    result = await AdminService.bulk_upload_users(current_user, payload, db)
    return AdminBulkUploadResult(**result)


@router.get("/users/export")
async def export_users(
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.export_users(current_user, db)


@router.get("/roles", response_model=list[AdminRolePermissionOut])
async def get_roles(
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminRolePermissionOut]:
    _ = current_user
    rows = await AdminService.get_roles(db)
    return [AdminRolePermissionOut.model_validate(row) for row in rows]


@router.post("/roles", response_model=AdminRolePermissionOut)
async def create_or_update_role(
    payload: AdminRolePermissionUpsert,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminRolePermissionOut:
    row = await AdminService.upsert_role(current_user, payload, db)
    return AdminRolePermissionOut.model_validate(row)


@router.put("/roles", response_model=list[AdminRolePermissionOut])
async def update_roles(
    payload: AdminRolePermissionsUpdate,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminRolePermissionOut]:
    rows = await AdminService.batch_update_roles(current_user, payload.roles, db)
    return [AdminRolePermissionOut.model_validate(row) for row in rows]


@router.delete("/roles/{role_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_key: str,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.delete_role(current_user, role_key, db)


@router.get("/org-structure", response_model=AdminOrgStructureOut)
async def get_org_structure(
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminOrgStructureOut:
    payload = await AdminService.get_org_structure(current_user, db)
    return AdminOrgStructureOut(**payload)


@router.get("/settings", response_model=AdminSystemSettingsOut)
async def get_settings(
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemSettingsOut:
    _ = current_user
    payload = await AdminService.get_settings(db)
    return AdminSystemSettingsOut(**payload)


@router.put("/settings", response_model=AdminSystemSettingsOut)
async def update_settings(
    payload: AdminSystemSettingsUpdate,
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemSettingsOut:
    updated = await AdminService.update_settings(current_user, payload, db)
    return AdminSystemSettingsOut(**updated)


@router.get("/audit-logs", response_model=list[AdminAuditLogOut])
async def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminAuditLogOut]:
    rows = await AdminService.get_audit_logs(current_user, db, limit=limit)
    return [
        AdminAuditLogOut(
            id=str(row.id),
            actor_user_id=str(row.actor_user_id),
            action=row.action,
            target_type=row.target_type,
            target_id=row.target_id,
            message=row.message,
            details=row.details,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/role-history", response_model=list[AdminAuditLogOut])
async def get_role_history(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminAuditLogOut]:
    rows = await AdminService.get_role_history(current_user, db, limit=limit)
    return [
        AdminAuditLogOut(
            id=str(row.id),
            actor_user_id=str(row.actor_user_id),
            action=row.action,
            target_type=row.target_type,
            target_id=row.target_id,
            message=row.message,
            details=row.details,
            created_at=row.created_at,
        )
        for row in rows
    ]
