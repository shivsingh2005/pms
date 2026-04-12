from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Employee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employees"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True)
    employee_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    designation: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    join_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    user = relationship("User", foreign_keys=[user_id])
    manager = relationship("User", foreign_keys=[manager_id])
