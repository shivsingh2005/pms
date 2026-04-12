from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.models.notification_log import Notification
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_notifications(
    unread: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if unread:
        stmt = stmt.where(Notification.is_read.is_(False))

    stmt = stmt.order_by(Notification.created_at.desc()).limit(100)
    try:
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
    except ProgrammingError:
        # Keep dashboards functional if the live DB notifications schema lags the ORM model.
        logger.exception("Notifications query failed due to schema mismatch; returning empty list")
        return {"notifications": [], "total": 0}

    return {
        "notifications": [
            {
                "id": str(row.id),
                "title": row.title,
                "message": row.message,
                "notification_type": row.notification_type,
                "is_read": row.is_read,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
            .values(is_read=True)
        )
        await db.commit()
    except ProgrammingError:
        logger.exception("Mark notification read failed due to schema mismatch")
        return {"updated": 0}

    return {"updated": int(result.rowcount or 0)}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await db.commit()
    except ProgrammingError:
        logger.exception("Mark all notifications read failed due to schema mismatch")
        return {"updated": 0}

    return {"updated": int(result.rowcount or 0)}
