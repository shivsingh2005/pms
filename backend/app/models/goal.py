from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import GoalStatus, GoalFramework


class Goal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goals"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weightage: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus, name="goal_status"), default=GoalStatus.draft, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    framework: Mapped[GoalFramework] = mapped_column(Enum(GoalFramework, name="goal_framework"), nullable=False)

    contributions = relationship("GoalContribution", back_populates="goal", cascade="all, delete-orphan")


class GoalContribution(Base, UUIDMixin):
    __tablename__ = "goal_contributions"

    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False, index=True)
    contributor_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)

    goal = relationship("Goal", back_populates="contributions")
