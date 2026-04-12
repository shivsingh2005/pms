from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Employee9Box(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employee_9box"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    performance_rating: Mapped[float] = mapped_column(Float, nullable=False)
    potential_rating: Mapped[float] = mapped_column(Float, nullable=False)
    box_position: Mapped[str] = mapped_column(String(10), nullable=False)
    talent_category: Mapped[str | None] = mapped_column(String, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    user = relationship("User")
    cycle = relationship("PerformanceCycle")
