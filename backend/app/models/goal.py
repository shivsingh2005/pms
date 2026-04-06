from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import GoalStatus, GoalFramework


class Goal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goals"

    cycle_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    assigned_to: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weightage: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus, name="goal_status"), default=GoalStatus.draft, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    framework: Mapped[GoalFramework] = mapped_column(Enum(GoalFramework, name="goal_framework"), nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    drift_flags: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    aop_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("annual_operating_plan.id"), nullable=True, index=True)
    aop_assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("aop_manager_assignments.id"), nullable=True, index=True)
    is_cascaded_from_leadership: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    leadership_target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    leadership_target_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cascade_source: Mapped[str | None] = mapped_column(String(20), nullable=True)

    contributions = relationship("GoalContribution", back_populates="goal", cascade="all, delete-orphan")


class GoalContribution(Base, UUIDMixin):
    __tablename__ = "goal_contributions"

    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False, index=True)
    contributor_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)

    goal = relationship("Goal", back_populates="contributions")


class GoalLineage(Base, UUIDMixin):
    __tablename__ = "goal_lineage"

    parent_goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    child_goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    contribution_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    employee_goal_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True, index=True)
    manager_goal_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True, index=True)
    aop_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("annual_operating_plan.id"), nullable=True, index=True)
    aop_assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("aop_manager_assignments.id"), nullable=True, index=True)
    employee_target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    employee_target_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    manager_target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    aop_total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    contribution_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)


class GoalChangeLog(Base, UUIDMixin):
    __tablename__ = "goal_change_logs"

    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    change_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
