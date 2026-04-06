from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AOPManagerAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "aop_manager_assignments"

    aop_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("annual_operating_plan.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_target_value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    assigned_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    target_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
