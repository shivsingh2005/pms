"""checkin workflow fields and status lifecycle

Revision ID: 20260322_0009
Revises: 20260321_0008
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "20260322_0009"
down_revision = "20260321_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires enum value additions to be committed before use.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE checkin_status ADD VALUE IF NOT EXISTS 'draft'")
        op.execute("ALTER TYPE checkin_status ADD VALUE IF NOT EXISTS 'submitted'")
        op.execute("ALTER TYPE checkin_status ADD VALUE IF NOT EXISTS 'reviewed'")

    op.execute("UPDATE checkins SET status = 'submitted' WHERE status = 'scheduled'")
    op.execute("UPDATE checkins SET status = 'reviewed' WHERE status = 'completed'")

    op.add_column("checkins", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("checkins", sa.Column("blockers", sa.Text(), nullable=True))
    op.add_column("checkins", sa.Column("next_steps", sa.Text(), nullable=True))
    op.add_column("checkins", sa.Column("manager_feedback", sa.Text(), nullable=True))
    op.add_column(
        "checkins",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_checkins_manager_id", "checkins", ["manager_id"], unique=False)
    op.create_index("ix_checkins_status", "checkins", ["status"], unique=False)
    op.create_check_constraint("ck_checkins_progress_range", "checkins", "progress >= 0 AND progress <= 100")

    op.alter_column("checkins", "meeting_date", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    op.alter_column("checkins", "meeting_date", existing_type=sa.DateTime(timezone=True), nullable=False)

    op.drop_constraint("ck_checkins_progress_range", "checkins", type_="check")
    op.drop_index("ix_checkins_status", table_name="checkins")
    op.drop_index("ix_checkins_manager_id", table_name="checkins")

    op.drop_column("checkins", "updated_at")
    op.drop_column("checkins", "manager_feedback")
    op.drop_column("checkins", "next_steps")
    op.drop_column("checkins", "blockers")
    op.drop_column("checkins", "progress")

    op.execute("UPDATE checkins SET status = 'scheduled' WHERE status = 'draft'")
    op.execute("UPDATE checkins SET status = 'scheduled' WHERE status = 'submitted'")
    op.execute("UPDATE checkins SET status = 'completed' WHERE status = 'reviewed'")
