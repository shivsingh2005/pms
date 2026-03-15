from datetime import datetime
from pydantic import BaseModel
from app.models.enums import CheckinStatus


class CheckinCreate(BaseModel):
    goal_id: str
    employee_id: str
    manager_id: str
    meeting_date: datetime
    meeting_link: str | None = None


class CheckinComplete(BaseModel):
    transcript: str | None = None
    summary: str | None = None


class CheckinOut(BaseModel):
    id: str
    goal_id: str
    employee_id: str
    manager_id: str
    meeting_date: datetime
    status: CheckinStatus
    meeting_link: str | None
    transcript: str | None
    summary: str | None

    model_config = {"from_attributes": True}
