from datetime import datetime
from sqlalchemy import ARRAY, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin
from app.models.enums import CheckinStatus


class Checkin(Base, UUIDMixin):
    __tablename__ = "checkins"

    cycle_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=True, index=True)
    goal_ids: Mapped[list[str]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    goal_updates: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    overall_progress: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(
        Enum(CheckinStatus, name="checkin_status"),
        default=CheckinStatus.draft,
        nullable=False,
        index=True,
    )
    meeting_link: Mapped[str | None] = mapped_column(String, nullable=True)
    meeting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manager_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_final: Mapped[bool] = mapped_column(nullable=False, default=False)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attachments: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    goal_rag_statuses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ai_agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("overall_progress >= 0 AND overall_progress <= 100", name="ck_checkins_overall_progress_range"),
        CheckConstraint("confidence_level IS NULL OR (confidence_level >= 1 AND confidence_level <= 5)", name="ck_checkins_confidence_range"),
        CheckConstraint("overall_confidence IS NULL OR (overall_confidence >= 1 AND overall_confidence <= 5)", name="ck_checkins_overall_confidence_range"),
    )
