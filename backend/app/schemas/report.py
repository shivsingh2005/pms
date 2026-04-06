from datetime import datetime
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(pattern="^(individual|team|business)$")
    employee_id: str | None = None
    manager_id: str | None = None


class ReportSection(BaseModel):
    heading: str
    content: list[str]


class ReportGenerateResponse(BaseModel):
    report_type: str
    generated_at: datetime
    summary: str
    sections: list[ReportSection]
    metadata: dict[str, str | int | float | None] = Field(default_factory=dict)
