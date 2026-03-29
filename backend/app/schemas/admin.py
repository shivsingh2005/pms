from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class AdminUserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    manager_id: str | None = None
    manager_name: str | None = None
    department: str | None = None
    title: str | None = None
    is_active: bool
    created_at: datetime


class AdminUsersListOut(BaseModel):
    users: list[AdminUserOut]
    managers: list[dict[str, str]]
    departments: list[str]


class AdminUserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: UserRole
    manager_id: str | None = None
    department: str | None = None
    title: str | None = None
    password: str | None = None


class AdminUserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    role: UserRole | None = None
    manager_id: str | None = None
    department: str | None = None
    title: str | None = None
    is_active: bool | None = None


class AdminBulkUserRow(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    manager_email: EmailStr | None = None
    department: str | None = None
    title: str | None = None


class AdminBulkUploadRequest(BaseModel):
    users: list[AdminBulkUserRow]


class AdminBulkUploadResult(BaseModel):
    created: int
    failed: int
    errors: list[str]


class AdminRolePermissionOut(BaseModel):
    role_key: str
    display_name: str
    permissions: list[str]
    is_system: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminRolePermissionUpsert(BaseModel):
    role_key: str
    display_name: str
    permissions: list[str]


class AdminRolePermissionsUpdate(BaseModel):
    roles: list[AdminRolePermissionUpsert]


class AdminManagerNode(BaseModel):
    manager_id: str
    manager_name: str
    department: str | None = None
    team_size: int
    avg_team_rating: float
    members: list[AdminUserOut]


class AdminOrgStructureOut(BaseModel):
    leaders: list[AdminUserOut]
    managers: list[AdminManagerNode]


class AdminSystemSettingsOut(BaseModel):
    working_hours: dict
    rating_scale: dict
    checkin_frequency: dict
    ai_settings: dict


class AdminSystemSettingsUpdate(BaseModel):
    working_hours: dict | None = None
    rating_scale: dict | None = None
    checkin_frequency: dict | None = None
    ai_settings: dict | None = None


class AdminDashboardMetricOut(BaseModel):
    total_employees: int
    total_managers: int
    active_users: int
    total_goals: int
    active_checkins: int
    meetings_scheduled: int
    avg_rating: float


class AdminDashboardOut(BaseModel):
    metrics: AdminDashboardMetricOut
    employee_growth: list[dict[str, int | str]]
    role_distribution: list[dict[str, int | str]]
    rating_distribution: list[dict[str, int | str]]


class AdminAuditLogOut(BaseModel):
    id: str
    actor_user_id: str
    action: str
    target_type: str
    target_id: str | None
    message: str
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}
