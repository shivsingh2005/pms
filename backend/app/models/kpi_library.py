from datetime import datetime
from sqlalchemy import String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class KPILibrary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kpi_libraries"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    expectations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    organization = relationship("Organization")
