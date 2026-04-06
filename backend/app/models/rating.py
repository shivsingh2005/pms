from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin
from app.models.enums import RatingLabel


class Rating(Base, UUIDMixin):
    __tablename__ = "ratings"

    cycle_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=True, index=True)
    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_label: Mapped[RatingLabel] = mapped_column(Enum(RatingLabel, name="rating_label"), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
