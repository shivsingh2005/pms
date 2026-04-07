from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import PerformanceCycleStatus


class PerformanceCycle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "performance_cycles"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cycle_type: Mapped[str] = mapped_column(String, nullable=False)  # quarterly | yearly | hybrid
    framework: Mapped[str] = mapped_column(String, nullable=False)  # OKR | MBO | Hybrid | custom
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    goal_setting_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    self_review_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    checkin_cap_per_quarter: Mapped[int] = mapped_column(default=5, nullable=False)
    ai_usage_cap_per_quarter: Mapped[int] = mapped_column(default=3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[PerformanceCycleStatus] = mapped_column(
        Enum(PerformanceCycleStatus, name="performance_cycle_status"),
        nullable=False,
        default=PerformanceCycleStatus.planning,
        index=True,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
