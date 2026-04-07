"""add meeting type and make goal optional on meetings

Revision ID: 20260325_0013
Revises: 20260324_0012
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260325_0013"
down_revision = "20260324_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    meeting_type = postgresql.ENUM("CHECKIN", "GENERAL", "HR", "REVIEW", name="meeting_type", create_type=False)
    meeting_type.create(bind, checkfirst=True)

    op.add_column(
        "meetings",
        sa.Column("meeting_type", meeting_type, nullable=True, server_default=sa.text("'GENERAL'")),
    )

    op.execute(
        """
        UPDATE meetings
        SET meeting_type = CASE
            WHEN goal_id IS NOT NULL THEN 'CHECKIN'::meeting_type
            ELSE 'GENERAL'::meeting_type
        END
        """
    )

    op.alter_column("meetings", "meeting_type", nullable=False, server_default=sa.text("'GENERAL'"))
    op.alter_column("meetings", "goal_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    # Restoring non-null goal_id requires cleanup of rows created without goals.
    op.execute("DELETE FROM meetings WHERE goal_id IS NULL")
    op.alter_column("meetings", "goal_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    op.drop_column("meetings", "meeting_type")

    bind = op.get_bind()
    sa.Enum(name="meeting_type").drop(bind, checkfirst=True)
