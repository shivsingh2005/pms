from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class EmployeeManagerMapping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employee_manager_mappings"

    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    employee = relationship("User", foreign_keys=[employee_id])
    manager = relationship("User", foreign_keys=[manager_id])
    organization = relationship("Organization")
