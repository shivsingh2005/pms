from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.checkin import Checkin
from app.models.enums import CheckinStatus, UserRole
from app.models.user import User
from app.schemas.checkin import CheckinComplete, CheckinCreate


class CheckinService:
    @staticmethod
    async def schedule(payload: CheckinCreate, db: AsyncSession) -> Checkin:
        checkin = Checkin(
            goal_id=payload.goal_id,
            employee_id=payload.employee_id,
            manager_id=payload.manager_id,
            meeting_date=payload.meeting_date,
            status=CheckinStatus.scheduled,
            meeting_link=payload.meeting_link,
            created_at=datetime.now(timezone.utc),
        )
        db.add(checkin)
        await db.commit()
        await db.refresh(checkin)
        return checkin

    @staticmethod
    async def list_checkins(current_user: User, db: AsyncSession) -> list[Checkin]:
        stmt = select(Checkin)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(Checkin.employee_id == current_user.id)
        elif current_user.role == UserRole.manager:
            stmt = stmt.where(Checkin.manager_id == current_user.id)
        else:
            stmt = stmt.where(
                (Checkin.employee_id == current_user.id) | (Checkin.manager_id == current_user.id)
            )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def complete(checkin_id: str, payload: CheckinComplete, db: AsyncSession) -> Checkin:
        checkin = await db.get(Checkin, checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        checkin.status = CheckinStatus.completed
        checkin.transcript = payload.transcript
        checkin.summary = payload.summary
        await db.commit()
        await db.refresh(checkin)
        return checkin
