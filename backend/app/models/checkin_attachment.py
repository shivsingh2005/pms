from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class CheckinAttachment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "checkin_attachments"

    checkin_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    checkin = relationship("Checkin")
    uploaded_by = relationship("User")
