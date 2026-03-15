from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    @staticmethod
    async def get_team(current_user: User, db: AsyncSession) -> list[User]:
        if current_user.role == UserRole.manager:
            result = await db.execute(select(User).where(User.manager_id == current_user.id))
            return list(result.scalars().all())

        if current_user.role in {UserRole.hr, UserRole.leadership, UserRole.admin}:
            result = await db.execute(select(User).where(User.organization_id == current_user.organization_id))
            return list(result.scalars().all())

        return []

    @staticmethod
    async def update_user(target_user: User, payload: UserUpdate, db: AsyncSession) -> User:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(target_user, key, value)
        await db.commit()
        await db.refresh(target_user)
        return target_user
