from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class MeetingProposal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "meeting_proposals"

    meeting_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False, index=True)
    proposed_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    is_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    meeting = relationship("Meeting")
    proposed_by = relationship("User")
