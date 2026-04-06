from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import UserRole


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    profile_picture: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.employee)
    roles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    manager_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    first_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    google_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    google_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="users")
    manager = relationship("User", remote_side="User.id")
