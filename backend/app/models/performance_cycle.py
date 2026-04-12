from datetime import datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import PerformanceCycleStatus


class PerformanceCycle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "performance_cycles"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cycle_type: Mapped[str] = mapped_column(String, nullable=False)
    framework: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    goal_setting_deadline: Mapped[datetime] = mapped_column(Date, nullable=False)
    self_review_deadline: Mapped[datetime] = mapped_column(Date, nullable=False)
    checkin_cap_per_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_usage_cap_per_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[PerformanceCycleStatus] = mapped_column(
        Enum(PerformanceCycleStatus, name="performance_cycle_status"),
        default=PerformanceCycleStatus.active,
        nullable=False,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    organization = relationship("Organization")
