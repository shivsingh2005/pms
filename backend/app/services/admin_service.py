from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, case, cast, Date, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.admin_audit_log import AdminAuditLog
from app.models.admin_role_permission import AdminRolePermission
from app.models.admin_system_setting import AdminSystemSetting
from app.models.checkin import Checkin
from app.models.enums import CheckinStatus, RatingLabel, UserRole
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.rating import Rating
from app.models.user import User
from app.schemas.admin import (
    AdminBulkUploadRequest,
    AdminRolePermissionUpsert,
    AdminSystemSettingsUpdate,
    AdminUserCreate,
    AdminUserUpdate,
)


class AdminService:
    DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
        "admin": [
            "users:create",
            "users:update",
            "users:delete",
            "users:assign_manager",
            "users:assign_role",
            "roles:manage",
            "org:view",
            "org:reassign",
            "settings:manage",
            "audit:view",
        ],
        "hr": ["users:view", "users:update", "org:view", "reports:view"],
        "manager": ["goals:create", "checkins:approve", "team:view"],
        "employee": ["checkins:submit", "goals:view"],
        "leadership": ["org:view", "reports:view", "insights:view"],
    }

    DEFAULT_SETTINGS: dict[str, dict] = {
        "working_hours": {"start": "09:00", "end": "18:00", "timezone": "UTC"},
        "rating_scale": {
            "min": 1,
            "max": 5,
            "labels": {"1": "NI", "2": "SME", "3": "ME", "4": "DE", "5": "EE"},
        },
        "checkin_frequency": {"mode": "weekly", "days": ["Friday"]},
        "ai_settings": {"provider": "gemini", "model": "gemini-2.5-flash", "api_key_masked": ""},
    }

    @staticmethod
    async def _log_action(
        db: AsyncSession,
        actor_user_id: UUID,
        action: str,
        target_type: str,
        message: str,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        db.add(
            AdminAuditLog(
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                message=message,
                details=details or {},
            )
        )

    @staticmethod
    async def _ensure_role_permissions(db: AsyncSession) -> None:
        result = await db.execute(select(AdminRolePermission.role_key))
        existing = set(result.scalars().all())

        now = datetime.now(timezone.utc)
        for role_key, permissions in AdminService.DEFAULT_ROLE_PERMISSIONS.items():
            if role_key in existing:
                continue
            db.add(
                AdminRolePermission(
                    role_key=role_key,
                    display_name=role_key.title(),
                    permissions=permissions,
                    is_system=True,
                    created_at=now,
                    updated_at=now,
                )
            )

    @staticmethod
    async def _ensure_system_settings(db: AsyncSession) -> None:
        result = await db.execute(select(AdminSystemSetting.key))
        existing = set(result.scalars().all())

        now = datetime.now(timezone.utc)
        for key, value in AdminService.DEFAULT_SETTINGS.items():
            if key in existing:
                continue
            db.add(AdminSystemSetting(key=key, value=value, updated_by=None, updated_at=now))

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        if not api_key:
            return ""
        if len(api_key) <= 6:
            return "*" * len(api_key)
        return f"{api_key[:3]}{'*' * (len(api_key) - 6)}{api_key[-3:]}"

    @staticmethod
    def _build_user_filters(
        stmt,
        organization_id: UUID,
        role: str | None,
        manager_id: str | None,
        department: str | None,
        status_filter: str | None,
        search: str | None,
    ):
        stmt = stmt.where(User.organization_id == organization_id)

        if role:
            try:
                stmt = stmt.where(User.role == UserRole(role))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role filter")

        if manager_id:
            try:
                stmt = stmt.where(User.manager_id == UUID(manager_id))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid manager_id")

        if department:
            stmt = stmt.where(func.lower(func.coalesce(User.department, "")) == department.lower())

        if status_filter == "active":
            stmt = stmt.where(User.is_active.is_(True))
        elif status_filter == "inactive":
            stmt = stmt.where(User.is_active.is_(False))

        if search:
            q = f"%{search.strip().lower()}%"
            stmt = stmt.where(or_(func.lower(User.name).like(q), func.lower(User.email).like(q)))

        return stmt

    @staticmethod
    async def get_dashboard(current_user: User, db: AsyncSession) -> dict:
        org_id = current_user.organization_id

        total_employees = int(
            (
                await db.execute(
                    select(func.count(User.id)).where(User.organization_id == org_id, User.role == UserRole.employee)
                )
            ).scalar()
            or 0
        )
        total_managers = int(
            (
                await db.execute(
                    select(func.count(User.id)).where(User.organization_id == org_id, User.role == UserRole.manager)
                )
            ).scalar()
            or 0
        )
        active_users = int(
            (
                await db.execute(select(func.count(User.id)).where(User.organization_id == org_id, User.is_active.is_(True)))
            ).scalar()
            or 0
        )

        user_ids_result = await db.execute(select(User.id).where(User.organization_id == org_id))
        user_ids = [row[0] for row in user_ids_result.all()]

        total_goals = 0
        active_checkins = 0
        meetings_scheduled = 0
        avg_rating = 0.0

        if user_ids:
            total_goals = int((await db.execute(select(func.count(Goal.id)).where(Goal.user_id.in_(user_ids)))).scalar() or 0)
            active_checkins = int(
                (
                    await db.execute(
                        select(func.count(Checkin.id)).where(
                            Checkin.employee_id.in_(user_ids),
                            Checkin.status.in_([CheckinStatus.submitted, CheckinStatus.reviewed]),
                        )
                    )
                ).scalar()
                or 0
            )
            meetings_scheduled = int(
                (
                    await db.execute(select(func.count(Meeting.id)).where(Meeting.employee_id.in_(user_ids)))
                ).scalar()
                or 0
            )
            avg_rating = round(float((await db.execute(select(func.avg(Rating.rating)).where(Rating.employee_id.in_(user_ids)))).scalar() or 0), 2)

        growth_bucket = cast(func.date_trunc("month", User.created_at), Date).label("month")
        growth_result = await db.execute(
            select(growth_bucket, func.count(User.id))
            .where(User.organization_id == org_id)
            .group_by(growth_bucket)
            .order_by(growth_bucket.asc())
        )
        employee_growth = [{"month": row[0].isoformat(), "count": int(row[1])} for row in growth_result.all()]

        role_result = await db.execute(
            select(User.role, func.count(User.id)).where(User.organization_id == org_id).group_by(User.role)
        )
        role_distribution = [{"role": row[0].value if hasattr(row[0], "value") else str(row[0]), "count": int(row[1])} for row in role_result.all()]

        rating_result = await db.execute(
            select(Rating.rating_label, func.count(Rating.id))
            .join(User, User.id == Rating.employee_id)
            .where(User.organization_id == org_id)
            .group_by(Rating.rating_label)
        )
        by_label = {
            (row[0].value if hasattr(row[0], "value") else str(row[0])): int(row[1]) for row in rating_result.all()
        }
        ordered_labels = [label.value for label in RatingLabel]
        rating_distribution = [{"label": label, "count": by_label.get(label, 0)} for label in ordered_labels]

        return {
            "metrics": {
                "total_employees": total_employees,
                "total_managers": total_managers,
                "active_users": active_users,
                "total_goals": total_goals,
                "active_checkins": active_checkins,
                "meetings_scheduled": meetings_scheduled,
                "avg_rating": avg_rating,
            },
            "employee_growth": employee_growth,
            "role_distribution": role_distribution,
            "rating_distribution": rating_distribution,
        }

    @staticmethod
    async def list_users(
        current_user: User,
        db: AsyncSession,
        role: str | None,
        manager_id: str | None,
        department: str | None,
        status_filter: str | None,
        search: str | None,
    ) -> dict:
        manager_alias = aliased(User)

        stmt = (
            select(User, manager_alias.name)
            .outerjoin(manager_alias, User.manager_id == manager_alias.id)
            .order_by(User.created_at.desc())
        )
        stmt = AdminService._build_user_filters(
            stmt,
            current_user.organization_id,
            role,
            manager_id,
            department,
            status_filter,
            search,
        )

        rows = (await db.execute(stmt)).all()

        users = [
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "manager_id": str(user.manager_id) if user.manager_id else None,
                "manager_name": manager_name,
                "department": user.department,
                "title": user.title,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user, manager_name in rows
        ]

        managers_stmt = select(User.id, User.name).where(
            User.organization_id == current_user.organization_id,
            User.role == UserRole.manager,
            User.is_active.is_(True),
        )
        managers_rows = (await db.execute(managers_stmt)).all()
        managers = [{"id": str(row[0]), "name": row[1]} for row in managers_rows]

        departments_result = await db.execute(
            select(User.department)
            .where(User.organization_id == current_user.organization_id, User.department.is_not(None))
            .group_by(User.department)
            .order_by(User.department.asc())
        )
        departments = [row[0] for row in departments_result.all() if row[0]]

        return {"users": users, "managers": managers, "departments": departments}

    @staticmethod
    async def create_user(current_user: User, payload: AdminUserCreate, db: AsyncSession) -> dict:
        existing = (
            await db.execute(
                select(User.id).where(
                    and_(
                        User.email == payload.email.lower().strip(),
                        User.organization_id == current_user.organization_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

        manager_uuid = None
        if payload.manager_id:
            try:
                manager_uuid = UUID(payload.manager_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid manager_id")

            manager = (
                await db.execute(
                    select(User).where(
                        User.id == manager_uuid,
                        User.organization_id == current_user.organization_id,
                        User.role == UserRole.manager,
                    )
                )
            ).scalar_one_or_none()
            if not manager:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

        generated_password = payload.password or f"Temp@{uuid4().hex[:10]}"
        new_user = User(
            google_id=f"local-{uuid4()}",
            email=payload.email.lower().strip(),
            name=payload.name.strip(),
            role=payload.role,
            roles=sorted({payload.role.value, UserRole.employee.value if payload.role == UserRole.manager else payload.role.value}),
            organization_id=current_user.organization_id,
            manager_id=manager_uuid,
            department=payload.department,
            title=payload.title,
            is_active=True,
        )
        db.add(new_user)
        await db.flush()

        await AdminService._log_action(
            db,
            current_user.id,
            "user.create",
            "user",
            f"Created user {new_user.email}",
            target_id=str(new_user.id),
            details={
                "role": new_user.role.value,
                "department": new_user.department,
                "manager_id": str(new_user.manager_id) if new_user.manager_id else None,
                "generated_password": generated_password,
            },
        )

        await db.commit()
        await db.refresh(new_user)

        manager_name = None
        if new_user.manager_id:
            manager_name = (
                await db.execute(select(User.name).where(User.id == new_user.manager_id))
            ).scalar_one_or_none()

        return {
            "id": str(new_user.id),
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "manager_id": str(new_user.manager_id) if new_user.manager_id else None,
            "manager_name": manager_name,
            "department": new_user.department,
            "title": new_user.title,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at,
        }

    @staticmethod
    async def update_user(current_user: User, user_id: str, payload: AdminUserUpdate, db: AsyncSession) -> dict:
        try:
            target_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id")

        target = (
            await db.execute(
                select(User).where(User.id == target_uuid, User.organization_id == current_user.organization_id)
            )
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if target.id == current_user.id and payload.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot deactivate own account")

        before = {
            "name": target.name,
            "email": target.email,
            "role": target.role.value,
            "manager_id": str(target.manager_id) if target.manager_id else None,
            "department": target.department,
            "title": target.title,
            "is_active": target.is_active,
        }

        if payload.manager_id is not None:
            if payload.manager_id == "":
                target.manager_id = None
            else:
                try:
                    manager_uuid = UUID(payload.manager_id)
                except ValueError:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid manager_id")

                if manager_uuid == target.id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User cannot report to themselves")

                manager = (
                    await db.execute(
                        select(User).where(
                            User.id == manager_uuid,
                            User.organization_id == current_user.organization_id,
                            User.role == UserRole.manager,
                        )
                    )
                ).scalar_one_or_none()
                if not manager:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
                target.manager_id = manager_uuid

        if payload.name is not None:
            target.name = payload.name.strip()
        if payload.email is not None:
            target.email = payload.email.lower().strip()
        if payload.department is not None:
            target.department = payload.department
        if payload.title is not None:
            target.title = payload.title
        if payload.is_active is not None:
            target.is_active = payload.is_active

        role_changed = False
        if payload.role is not None and payload.role != target.role:
            role_changed = True
            target.role = payload.role
            target.roles = sorted({payload.role.value, UserRole.employee.value if payload.role == UserRole.manager else payload.role.value})

        await AdminService._log_action(
            db,
            current_user.id,
            "user.update",
            "user",
            f"Updated user {target.email}",
            target_id=str(target.id),
            details={
                "before": before,
                "after": {
                    "name": target.name,
                    "email": target.email,
                    "role": target.role.value,
                    "manager_id": str(target.manager_id) if target.manager_id else None,
                    "department": target.department,
                    "title": target.title,
                    "is_active": target.is_active,
                },
            },
        )

        if role_changed:
            await AdminService._log_action(
                db,
                current_user.id,
                "role.change",
                "user",
                f"Changed role for {target.email}",
                target_id=str(target.id),
                details={"new_role": target.role.value},
            )

        await db.commit()
        await db.refresh(target)

        manager_name = None
        if target.manager_id:
            manager_name = (await db.execute(select(User.name).where(User.id == target.manager_id))).scalar_one_or_none()

        return {
            "id": str(target.id),
            "name": target.name,
            "email": target.email,
            "role": target.role,
            "manager_id": str(target.manager_id) if target.manager_id else None,
            "manager_name": manager_name,
            "department": target.department,
            "title": target.title,
            "is_active": target.is_active,
            "created_at": target.created_at,
        }

    @staticmethod
    async def soft_delete_user(current_user: User, user_id: str, db: AsyncSession) -> None:
        try:
            target_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id")

        target = (
            await db.execute(
                select(User).where(User.id == target_uuid, User.organization_id == current_user.organization_id)
            )
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if target.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot delete own account")

        target.is_active = False

        await AdminService._log_action(
            db,
            current_user.id,
            "user.soft_delete",
            "user",
            f"Deactivated user {target.email}",
            target_id=str(target.id),
            details={"email": target.email},
        )

        await db.commit()

    @staticmethod
    async def bulk_upload_users(current_user: User, payload: AdminBulkUploadRequest, db: AsyncSession) -> dict:
        manager_map_result = await db.execute(
            select(func.lower(User.email), User.id).where(
                User.organization_id == current_user.organization_id,
                User.role == UserRole.manager,
            )
        )
        manager_map = {row[0]: row[1] for row in manager_map_result.all()}

        created = 0
        failed = 0
        errors: list[str] = []

        for idx, row in enumerate(payload.users, start=1):
            existing = (
                await db.execute(
                    select(User.id).where(
                        User.organization_id == current_user.organization_id,
                        func.lower(User.email) == row.email.lower(),
                    )
                )
            ).scalar_one_or_none()
            if existing:
                failed += 1
                errors.append(f"Row {idx}: email already exists ({row.email})")
                continue

            manager_id = None
            if row.manager_email:
                manager_id = manager_map.get(row.manager_email.lower())
                if not manager_id:
                    failed += 1
                    errors.append(f"Row {idx}: manager not found ({row.manager_email})")
                    continue

            db.add(
                User(
                    google_id=f"bulk-{uuid4()}",
                    email=row.email.lower(),
                    name=row.name.strip(),
                    role=row.role,
                    roles=sorted({row.role.value, UserRole.employee.value if row.role == UserRole.manager else row.role.value}),
                    organization_id=current_user.organization_id,
                    manager_id=manager_id,
                    department=row.department,
                    title=row.title,
                    is_active=True,
                )
            )
            created += 1

        await AdminService._log_action(
            db,
            current_user.id,
            "user.bulk_upload",
            "user",
            f"Bulk upload processed ({created} created, {failed} failed)",
            details={"created": created, "failed": failed, "errors": errors[:20]},
        )

        await db.commit()
        return {"created": created, "failed": failed, "errors": errors}

    @staticmethod
    async def export_users(current_user: User, db: AsyncSession) -> list[dict]:
        manager_alias = aliased(User)
        rows = (
            await db.execute(
                select(User, manager_alias.name)
                .outerjoin(manager_alias, User.manager_id == manager_alias.id)
                .where(User.organization_id == current_user.organization_id)
                .order_by(User.name.asc())
            )
        ).all()

        return [
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "manager": manager_name,
                "department": user.department,
                "status": "active" if user.is_active else "inactive",
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            for user, manager_name in rows
        ]

    @staticmethod
    async def get_roles(db: AsyncSession) -> list[AdminRolePermission]:
        await AdminService._ensure_role_permissions(db)
        await db.commit()
        rows = (await db.execute(select(AdminRolePermission).order_by(AdminRolePermission.role_key.asc()))).scalars().all()
        return list(rows)

    @staticmethod
    async def upsert_role(current_user: User, payload: AdminRolePermissionUpsert, db: AsyncSession) -> AdminRolePermission:
        role = (
            await db.execute(select(AdminRolePermission).where(AdminRolePermission.role_key == payload.role_key.strip().lower()))
        ).scalar_one_or_none()

        if role:
            role.display_name = payload.display_name.strip()
            role.permissions = sorted(set(payload.permissions))
            role.updated_at = datetime.now(timezone.utc)
            action = "role.update"
            message = f"Updated role {role.role_key}"
        else:
            role = AdminRolePermission(
                role_key=payload.role_key.strip().lower(),
                display_name=payload.display_name.strip(),
                permissions=sorted(set(payload.permissions)),
                is_system=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(role)
            action = "role.create"
            message = f"Created role {role.role_key}"

        await AdminService._log_action(
            db,
            current_user.id,
            action,
            "role",
            message,
            target_id=role.role_key,
            details={"permissions": role.permissions},
        )

        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def batch_update_roles(current_user: User, roles: list[AdminRolePermissionUpsert], db: AsyncSession) -> list[AdminRolePermission]:
        updated: list[AdminRolePermission] = []
        for role in roles:
            updated.append(await AdminService.upsert_role(current_user, role, db))
        return updated

    @staticmethod
    async def delete_role(current_user: User, role_key: str, db: AsyncSession) -> None:
        role = (
            await db.execute(select(AdminRolePermission).where(AdminRolePermission.role_key == role_key.strip().lower()))
        ).scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role.is_system:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System role cannot be deleted")

        await db.delete(role)
        await AdminService._log_action(
            db,
            current_user.id,
            "role.delete",
            "role",
            f"Deleted role {role.role_key}",
            target_id=role.role_key,
        )
        await db.commit()

    @staticmethod
    async def get_org_structure(current_user: User, db: AsyncSession) -> dict:
        leaders = (
            await db.execute(
                select(User)
                .where(
                    User.organization_id == current_user.organization_id,
                    User.role.in_([UserRole.leadership, UserRole.admin]),
                    User.is_active.is_(True),
                )
                .order_by(User.name.asc())
            )
        ).scalars().all()

        managers = (
            await db.execute(
                select(User)
                .where(
                    User.organization_id == current_user.organization_id,
                    User.role == UserRole.manager,
                    User.is_active.is_(True),
                )
                .order_by(User.name.asc())
            )
        ).scalars().all()

        manager_nodes = []
        for manager in managers:
            members = (
                await db.execute(
                    select(User).where(
                        User.organization_id == current_user.organization_id,
                        User.manager_id == manager.id,
                    )
                )
            ).scalars().all()

            member_ids = [member.id for member in members]
            avg_team_rating = 0.0
            if member_ids:
                avg_team_rating = round(
                    float((await db.execute(select(func.avg(Rating.rating)).where(Rating.employee_id.in_(member_ids)))).scalar() or 0),
                    2,
                )

            manager_nodes.append(
                {
                    "manager_id": str(manager.id),
                    "manager_name": manager.name,
                    "department": manager.department,
                    "team_size": len(members),
                    "avg_team_rating": avg_team_rating,
                    "members": [
                        {
                            "id": str(member.id),
                            "name": member.name,
                            "email": member.email,
                            "role": member.role,
                            "manager_id": str(member.manager_id) if member.manager_id else None,
                            "manager_name": manager.name,
                            "department": member.department,
                            "title": member.title,
                            "is_active": member.is_active,
                            "created_at": member.created_at,
                        }
                        for member in members
                    ],
                }
            )

        leader_payload = [
            {
                "id": str(leader.id),
                "name": leader.name,
                "email": leader.email,
                "role": leader.role,
                "manager_id": str(leader.manager_id) if leader.manager_id else None,
                "manager_name": None,
                "department": leader.department,
                "title": leader.title,
                "is_active": leader.is_active,
                "created_at": leader.created_at,
            }
            for leader in leaders
        ]

        return {"leaders": leader_payload, "managers": manager_nodes}

    @staticmethod
    async def get_settings(db: AsyncSession) -> dict:
        await AdminService._ensure_system_settings(db)
        await db.commit()

        rows = (await db.execute(select(AdminSystemSetting))).scalars().all()
        by_key = {row.key: row.value for row in rows}

        return {
            "working_hours": by_key.get("working_hours", AdminService.DEFAULT_SETTINGS["working_hours"]),
            "rating_scale": by_key.get("rating_scale", AdminService.DEFAULT_SETTINGS["rating_scale"]),
            "checkin_frequency": by_key.get("checkin_frequency", AdminService.DEFAULT_SETTINGS["checkin_frequency"]),
            "ai_settings": by_key.get("ai_settings", AdminService.DEFAULT_SETTINGS["ai_settings"]),
        }

    @staticmethod
    async def update_settings(current_user: User, payload: AdminSystemSettingsUpdate, db: AsyncSession) -> dict:
        await AdminService._ensure_system_settings(db)

        updates = payload.model_dump(exclude_none=True)
        if "ai_settings" in updates and isinstance(updates["ai_settings"], dict):
            ai_settings = updates["ai_settings"]
            raw_key = ai_settings.get("api_key")
            if isinstance(raw_key, str):
                ai_settings["api_key_masked"] = AdminService._mask_api_key(raw_key)
                ai_settings.pop("api_key", None)

        now = datetime.now(timezone.utc)
        for key, value in updates.items():
            row = (await db.execute(select(AdminSystemSetting).where(AdminSystemSetting.key == key))).scalar_one_or_none()
            if not row:
                row = AdminSystemSetting(key=key, value=value, updated_by=current_user.id, updated_at=now)
                db.add(row)
            else:
                row.value = value
                row.updated_by = current_user.id
                row.updated_at = now

        await AdminService._log_action(
            db,
            current_user.id,
            "settings.update",
            "settings",
            "Updated system settings",
            details={"keys": sorted(updates.keys())},
        )

        await db.commit()
        return await AdminService.get_settings(db)

    @staticmethod
    async def get_audit_logs(current_user: User, db: AsyncSession, limit: int = 100) -> list[AdminAuditLog]:
        rows = (
            await db.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.actor_user_id.is_not(None))
                .order_by(AdminAuditLog.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    @staticmethod
    async def get_role_history(current_user: User, db: AsyncSession, limit: int = 100) -> list[AdminAuditLog]:
        rows = (
            await db.execute(
                select(AdminAuditLog)
                .where(
                    or_(
                        AdminAuditLog.action == "role.change",
                        AdminAuditLog.action == "role.create",
                        AdminAuditLog.action == "role.update",
                        AdminAuditLog.action == "role.delete",
                    )
                )
                .order_by(AdminAuditLog.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)
