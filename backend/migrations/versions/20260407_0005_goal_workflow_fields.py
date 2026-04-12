"""add missing goal workflow fields

Revision ID: 20260407_0005
Revises: 20260316_0004
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260407_0005"
down_revision = "20260316_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "goals",
        sa.Column(
            "source_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'manager_assigned'"),
        ),
    )
    op.add_column("goals", sa.Column("submission_notes", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("manager_comment", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("ai_assessment", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("goals", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("edit_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("last_action_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_goals_last_action_by_users",
        "goals",
        "users",
        ["last_action_by"],
        ["id"],
    )
    op.create_index("ix_goals_last_action_by", "goals", ["last_action_by"])


def downgrade() -> None:
    op.drop_index("ix_goals_last_action_by", table_name="goals")
    op.drop_constraint("fk_goals_last_action_by_users", "goals", type_="foreignkey")
    op.drop_column("goals", "last_action_by")
    op.drop_column("goals", "withdrawn_at")
    op.drop_column("goals", "edit_requested_at")
    op.drop_column("goals", "rejected_at")
    op.drop_column("goals", "approved_at")
    op.drop_column("goals", "submitted_at")
    op.drop_column("goals", "ai_assessment")
    op.drop_column("goals", "manager_comment")
    op.drop_column("goals", "submission_notes")
    op.drop_column("goals", "source_type")
