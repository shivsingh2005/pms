from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationCreate


class OrganizationService:
    @staticmethod
    async def create_organization(payload: OrganizationCreate, db: AsyncSession) -> Organization:
        result = await db.execute(select(Organization).where(Organization.domain == payload.domain))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain already exists")

        org = Organization(name=payload.name, domain=payload.domain)
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def assign_user(org_id: str, user_id: str, db: AsyncSession) -> User:
        org = await db.get(Organization, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.organization_id = org.id
        await db.commit()
        await db.refresh(user)
        return user
