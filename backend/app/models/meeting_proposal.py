from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin
from app.models.enums import MeetingProposalStatus


class MeetingProposal(Base, UUIDMixin):
    __tablename__ = "meeting_proposals"

    checkin_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    manager_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    proposed_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    proposed_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[MeetingProposalStatus] = mapped_column(
        Enum(MeetingProposalStatus, name="meeting_proposal_status"),
        nullable=False,
        default=MeetingProposalStatus.pending,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
