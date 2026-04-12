from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class CycleTimeline(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cycle_timelines"

    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    phase_name: Mapped[str] = mapped_column(String, nullable=False)
    phase_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order: Mapped[int] = mapped_column(nullable=False, default=0)
    
    cycle = relationship("PerformanceCycle")
