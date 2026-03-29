from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin
from app.models.enums import MeetingStatus, MeetingType


class Meeting(Base, UUIDMixin):
    __tablename__ = "meetings"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organizer_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    checkin_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=True, index=True)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    manager_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    meeting_type: Mapped[MeetingType] = mapped_column(
        Enum(MeetingType, name="meeting_type"),
        nullable=False,
        default=MeetingType.GENERAL,
    )
    goal_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    google_event_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    meet_link: Mapped[str | None] = mapped_column(String, nullable=True)
    google_meet_link: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    participants: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, name="meeting_status"),
        nullable=False,
        default=MeetingStatus.scheduled,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
