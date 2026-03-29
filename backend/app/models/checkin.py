from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin
from app.models.enums import CheckinStatus


class Checkin(Base, UUIDMixin):
    __tablename__ = "checkins"

    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(
        Enum(CheckinStatus, name="checkin_status"),
        default=CheckinStatus.draft,
        nullable=False,
        index=True,
    )
    meeting_link: Mapped[str | None] = mapped_column(String, nullable=True)
    meeting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_checkins_progress_range"),
    )
