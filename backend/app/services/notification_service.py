from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_log import Notification
from app.models.user import User


class NotificationService:
    @staticmethod
    async def list_for_user(current_user: User, db: AsyncSession, unread_only: bool = False, limit: int = 25) -> dict:
        stmt = select(Notification).where(Notification.user_id == current_user.id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)

        items_result = await db.execute(stmt)
        items = list(items_result.scalars().all())

        unread_result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
        unread_count = int(unread_result.scalar() or 0)

        return {"unread_count": unread_count, "items": items}

    @staticmethod
    async def mark_read(notification_id: str, current_user: User, db: AsyncSession) -> None:
        await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
            .values(is_read=True)
        )
        await db.commit()

    @staticmethod
    async def mark_all_read(current_user: User, db: AsyncSession) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await db.commit()
        return int(result.rowcount or 0)
