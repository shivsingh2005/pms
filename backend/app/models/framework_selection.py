from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserFrameworkSelection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_framework_selections"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_framework: Mapped[str] = mapped_column(String, nullable=False)
    cycle_type: Mapped[str] = mapped_column(String, nullable=False, default="quarterly")
    recommendation_reason: Mapped[str | None] = mapped_column(String, nullable=True)


class DepartmentFrameworkPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "department_framework_policies"

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String, nullable=False, index=True)
    allowed_frameworks: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    cycle_type: Mapped[str] = mapped_column(String, nullable=False, default="quarterly")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "department", name="uq_department_framework_policies_org_department"),
    )
