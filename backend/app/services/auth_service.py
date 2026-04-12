from uuid import uuid4
from datetime import datetime, timezone
import logging
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.core.role_context import get_user_roles
from app.core.security import create_access_token, create_refresh_token
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import EmailLoginRequest, LoginUserResponse, TokenResponse


settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def _infer_role_from_email(email: str) -> UserRole:
        local_part = email.split("@")[0].strip().lower()
        if any(token in local_part for token in ("executive", "leadership", "admin", "director")):
            return UserRole.leadership
        if any(token in local_part for token in ("manager", "mgr", "lead")):
            return UserRole.manager
        if "hr" in local_part or "people" in local_part:
            return UserRole.hr
        return UserRole.employee

    @staticmethod
    def _resolved_roles(primary_role: UserRole) -> list[str]:
        roles: list[str] = [primary_role.value]
        if primary_role == UserRole.manager and UserRole.employee.value not in roles:
            roles.append(UserRole.employee.value)
        return roles

    @staticmethod
    async def _build_token_response(user: User) -> TokenResponse:
        token = create_access_token(
            {
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
                "role": user.role.value,
                "roles": sorted(role.value for role in get_user_roles(user)),
            }
        )
        refresh_token = create_refresh_token(
            {
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
                "role": user.role.value,
                "roles": sorted(role.value for role in get_user_roles(user)),
            }
        )
        resolved_roles = sorted(get_user_roles(user), key=lambda role: role.value)
        return TokenResponse(
            access_token=token,
            refresh_token=refresh_token,
            user=LoginUserResponse(
                id=user.id,
                name=user.name,
                role=user.role,
                email=user.email,
                roles=resolved_roles,
                domain=user.domain,
                business_unit=user.business_unit,
                department=user.department,
                title=user.title,
                manager_id=user.manager_id,
                first_login=user.first_login,
                onboarding_complete=user.onboarding_complete,
                last_active=user.last_active.isoformat() if user.last_active else None,
            ),
            user_id=user.id,
            name=user.name,
            role=user.role,
            roles=resolved_roles,
        )

    @staticmethod
    async def email_login(payload: EmailLoginRequest, db: AsyncSession) -> TokenResponse:
        raw_email = str(payload.email)
        email = raw_email.strip().lower()
        is_demo_email = email.endswith("@structured.mock") or email.endswith("@acmepms.com")
        should_infer_role = settings.APP_ENV.strip().lower() == "development" or is_demo_email

        logger.info("Auth login attempt received", extra={"email_raw": raw_email, "email_normalized": email})

        result = await db.execute(
            select(User).where(
                func.lower(func.btrim(User.email)) == email,
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()

        if user:
            logger.info("Auth login user matched", extra={"email_normalized": email, "user_id": str(user.id)})
        else:
            total_users = await db.execute(select(func.count(User.id)))
            logger.warning(
                "Auth login user not found",
                extra={
                    "email_normalized": email,
                    "total_users": int(total_users.scalar() or 0),
                },
            )

        if not user:
            if not should_infer_role:
                raise ValueError("User not registered")

            domain = email.split("@")[-1]
            org_result = await db.execute(select(Organization).where(Organization.domain == domain))
            org = org_result.scalar_one_or_none()

            if not org:
                org = Organization(name=domain.split(".")[0].title(), domain=domain)
                db.add(org)
                await db.flush()

            local_part = email.split("@")[0]
            inferred_name = " ".join(part.capitalize() for part in local_part.replace(".", " ").replace("_", " ").split())
            if not inferred_name:
                inferred_name = "Employee"

            inferred_role = AuthService._infer_role_from_email(email)
            user = User(
                google_id=f"email-{uuid4()}",
                email=email,
                name=inferred_name,
                profile_picture=None,
                role=inferred_role,
                roles=AuthService._resolved_roles(inferred_role),
                organization_id=org.id,
                domain=domain,
                first_login=True,
                onboarding_complete=False,
                last_active=datetime.now(timezone.utc),
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Keep seeded/demo data usable in development where legacy seed sets may have mismatched roles.
            if should_infer_role:
                inferred_role = AuthService._infer_role_from_email(email)
                if user.role != inferred_role:
                    user.role = inferred_role
                expected_roles = AuthService._resolved_roles(user.role)
                if sorted(user.roles or []) != sorted(expected_roles):
                    user.roles = expected_roles

        user.last_active = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        return await AuthService._build_token_response(user)
