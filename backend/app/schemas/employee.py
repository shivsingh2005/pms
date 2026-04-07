from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole


class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    email: EmailStr
    role: UserRole
    title: str | None = None
    department: str | None = None
    manager_id: str | None = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    employee_code: str | None = None
    name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    title: str | None = None
    department: str | None = None
    manager_id: str | None = None
    is_active: bool | None = None


class EmployeeOut(BaseModel):
    id: str
    employee_code: str
    name: str
    email: EmailStr
    role: UserRole
    title: str | None = None
    department: str | None = None
    manager_id: str | None = None
    is_active: bool
    team_size: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
