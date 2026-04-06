from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class KPILibrary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kpi_library"

    role: Mapped[str] = mapped_column(String, nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    goal_title: Mapped[str] = mapped_column(String, nullable=False)
    goal_description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_kpi: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_weight: Mapped[float] = mapped_column(nullable=False)
    framework: Mapped[str] = mapped_column(String, nullable=False, index=True)
