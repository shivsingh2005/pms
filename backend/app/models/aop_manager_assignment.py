from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class AOPManagerAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "aop_manager_assignments"

    aop_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("annual_operating_plan.id"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_target_value: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    assigned_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    target_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    aop = relationship("AnnualOperatingPlan")
    manager = relationship("User", foreign_keys=[manager_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
