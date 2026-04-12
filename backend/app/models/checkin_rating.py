from datetime import datetime
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class CheckinRating(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "checkin_ratings"

    checkin_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=False, index=True)
    rated_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    checkin = relationship("Checkin")
    rated_by = relationship("User")
