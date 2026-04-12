from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class SuccessionPlanning(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "succession_planning"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    position_title: Mapped[str] = mapped_column(String, nullable=False)
    current_holder_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    successor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    readiness_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    development_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    organization = relationship("Organization")
    current_holder = relationship("User", foreign_keys=[current_holder_id])
    successor = relationship("User", foreign_keys=[successor_id])
