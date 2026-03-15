"""add meetings table

Revision ID: 20260314_0003
Revises: 20260314_0002
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260314_0003"
down_revision = "20260314_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    meeting_status = postgresql.ENUM("scheduled", "completed", "cancelled", name="meeting_status", create_type=False)
    bind = op.get_bind()
    meeting_status.create(bind, checkfirst=True)

    op.create_table(
        "meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organizer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("goals.id"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("google_event_id", sa.String(), nullable=False, unique=True),
        sa.Column("google_meet_link", sa.String(), nullable=True),
        sa.Column("participants", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", meeting_status, nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_meetings_organizer_id", "meetings", ["organizer_id"])
    op.create_index("ix_meetings_goal_id", "meetings", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_meetings_goal_id", table_name="meetings")
    op.drop_index("ix_meetings_organizer_id", table_name="meetings")
    op.drop_table("meetings")

    bind = op.get_bind()
    sa.Enum(name="meeting_status").drop(bind, checkfirst=True)
