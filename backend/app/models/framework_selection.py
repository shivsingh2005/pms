from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class UserFrameworkSelection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_framework_selections"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    framework_type: Mapped[str] = mapped_column(String, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    user = relationship("User")
    cycle = relationship("PerformanceCycle")


class DepartmentFrameworkPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "department_framework_policies"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String, nullable=False)
    framework_type: Mapped[str] = mapped_column(String, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    organization = relationship("Organization")
    cycle = relationship("PerformanceCycle")
