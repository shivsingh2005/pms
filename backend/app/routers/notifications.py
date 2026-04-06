from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification import NotificationsListResponse
from app.services.notification_service import NotificationService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsListResponse)
async def list_notifications(
    unread: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationsListResponse:
    payload = await NotificationService.list_for_user(current_user, db, unread_only=unread)
    return NotificationsListResponse(**payload)


@router.post("/mark-read/{notification_id}")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await NotificationService.mark_read(notification_id, current_user, db)
    return {"ok": True}


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    updated = await NotificationService.mark_all_read(current_user, db)
    return {"ok": True, "updated": updated}
