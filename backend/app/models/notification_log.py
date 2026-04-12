from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    user = relationship("User")


class EmailLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_logs"

    recipient_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
