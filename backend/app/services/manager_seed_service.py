from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class ManagerSeedService:
    """Lightweight seed helpers used by manager dashboard resilience flows.

    The production-grade seeding logic was removed in a previous refactor. These
    fallbacks keep service orchestration stable while preserving DB-backed reads.
    """

    @staticmethod
    async def seed_manager_data(current_user: User, db: AsyncSession, team_size: int = 10) -> int:
        _ = (current_user, db, team_size)
        return 0

    @staticmethod
    async def seed_activity_for_existing_team(current_user: User, db: AsyncSession) -> int:
        _ = (current_user, db)
        return 0
