from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import UserRole


class Employee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employees"

    employee_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.employee)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    first_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    selected_framework: Mapped[str] = mapped_column(String, nullable=False, default="OKR")
    cycle_type: Mapped[str] = mapped_column(String, nullable=False, default="quarterly")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    manager = relationship("Employee", remote_side="Employee.id", back_populates="direct_reports")
    direct_reports = relationship("Employee", back_populates="manager")
