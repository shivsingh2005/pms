from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class GoalCluster(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goal_clusters"

    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    cycle = relationship("PerformanceCycle")
    organization = relationship("Organization")
