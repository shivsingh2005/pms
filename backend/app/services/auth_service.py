from uuid import uuid4
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
            is_development = settings.APP_ENV.strip().lower() == "development"
            if not is_development:
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

            user = User(
                google_id=f"email-{uuid4()}",
                email=email,
                name=inferred_name,
                profile_picture=None,
                role=UserRole.employee,
                roles=[UserRole.employee.value],
                organization_id=org.id,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return await AuthService._build_token_response(user)
