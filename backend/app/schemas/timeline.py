from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CycleTimelineNodeOut(BaseModel):
    id: UUID
    node_name: str
    status: str
    completed_at: datetime | None = None
    locked_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class CycleTimelineResponse(BaseModel):
    employee_id: UUID
    cycle_id: UUID
    items: list[CycleTimelineNodeOut]
