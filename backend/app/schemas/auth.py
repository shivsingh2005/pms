from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.models.enums import UserRole


class EmailLoginRequest(BaseModel):
    email: EmailStr


class LoginUserResponse(BaseModel):
    id: UUID
    name: str
    role: UserRole
    email: EmailStr | None = None
    roles: list[UserRole] = Field(default_factory=list)
    domain: str | None = None
    business_unit: str | None = None
    department: str | None = None
    title: str | None = None
    manager_id: UUID | None = None
    first_login: bool = True
    onboarding_complete: bool = False
    last_active: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: LoginUserResponse
    user_id: UUID | None = None
    name: str | None = None
    role: UserRole | None = None
    roles: list[UserRole] = Field(default_factory=list)


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthorizeResponse(BaseModel):
    authorization_url: str


class GoogleTokenExchangeRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


class GoogleTokenExchangeResponse(BaseModel):
    connected: bool
    expires_in: int | None = None
    scope: str | None = None


class GoogleConnectionStatusResponse(BaseModel):
    connected: bool
    token_expiry: str | None = None


class AuthUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    roles: list[UserRole] = Field(default_factory=list)
    organization_id: UUID
    manager_id: UUID | None = None
    domain: str | None = None
    business_unit: str | None = None
    department: str | None = None
    title: str | None = None
    first_login: bool = True
    onboarding_complete: bool = False
    last_active: str | None = None

    model_config = {"from_attributes": True}
