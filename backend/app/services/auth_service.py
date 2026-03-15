from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RoleLoginRequest, TokenResponse


class AuthService:
    @staticmethod
    async def role_login(payload: RoleLoginRequest, db: AsyncSession) -> TokenResponse:
        email = payload.email or f"{payload.role.value}@demo.local"
        name = payload.name or payload.role.value.title()

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            org = None
            if payload.organization_domain:
                org_result = await db.execute(
                    select(Organization).where(Organization.domain == payload.organization_domain)
                )
                org = org_result.scalar_one_or_none()

            if not org:
                domain = email.split("@")[-1]
                org_result = await db.execute(select(Organization).where(Organization.domain == domain))
                org = org_result.scalar_one_or_none()

            if not org:
                org = Organization(name=domain.split(".")[0].title(), domain=domain)
                db.add(org)
                await db.flush()

            user = User(
                google_id=f"role-{uuid4()}",
                email=email,
                name=name,
                profile_picture=None,
                role=payload.role,
                organization_id=org.id,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        elif user.role != payload.role:
            user.role = payload.role
            await db.commit()
            await db.refresh(user)

        token = create_access_token(
            {
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
                "role": user.role.value,
            }
        )
        refresh_token = create_refresh_token(
            {
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
                "role": user.role.value,
            }
        )
        return TokenResponse(access_token=token, refresh_token=refresh_token)
