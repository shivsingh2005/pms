from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    organization_id: str
    manager_id: str | None = None
    department: str | None = None
    title: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    profile_picture: str | None = None
    manager_id: str | None = None
    department: str | None = None
    title: str | None = None
    role: UserRole | None = None
