from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from app.models.base import Base, TimestampMixin, UUIDMixin


class AnnualOperatingPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "annual_operating_plan"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    name = synonym("title")
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_value: Mapped[str | None] = mapped_column(String, nullable=True)
    target_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    target_metric: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    
    organization = relationship("Organization")
    cycle = relationship("PerformanceCycle")
