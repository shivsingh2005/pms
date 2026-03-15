from datetime import datetime
from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    domain: str


class OrganizationAssignUser(BaseModel):
    user_id: str


class OrganizationOut(BaseModel):
    id: str
    name: str
    domain: str
    created_at: datetime

    model_config = {"from_attributes": True}
