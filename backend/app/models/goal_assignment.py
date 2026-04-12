from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import GoalStatus


class GoalAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goal_assignments"

    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False, index=True)
    assigned_to_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus, name="goal_status"), default=GoalStatus.draft, nullable=False)
    weightage: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    goal = relationship("Goal")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
