from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Employee9Box(Base, UUIDMixin):
    __tablename__ = "employee_9box"

    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id", ondelete="SET NULL"), nullable=True, index=True)
    performance_axis: Mapped[str] = mapped_column(String(10), nullable=False)
    potential_axis: Mapped[str] = mapped_column(String(10), nullable=False)
    box_label: Mapped[str] = mapped_column(String(30), nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)
    potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
