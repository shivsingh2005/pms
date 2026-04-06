from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class SuccessionPlanning(Base, UUIDMixin):
    __tablename__ = "succession_planning"

    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    readiness_score: Mapped[float] = mapped_column(nullable=False)
    readiness_level: Mapped[str] = mapped_column(String(20), nullable=False)
    gaps: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    development_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    nominated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
