"""Add self-goal approval workflow fields and history table.

Revision ID: 20260406_0027
Revises: 20260403_0026
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_0027"
down_revision = "20260403_0026"
branch_labels = None
depends_on = None


NEW_GOAL_STATUS_VALUES = [
    "pending_approval",
    "edit_requested",
    "withdrawn",
]


def upgrade() -> None:
    for value in NEW_GOAL_STATUS_VALUES:
        op.execute(
            sa.text(
                "ALTER TYPE goal_status ADD VALUE IF NOT EXISTS :value"
            ).bindparams(value=value)
        )

    op.add_column("goals", sa.Column("source_type", sa.String(length=20), nullable=False, server_default="manager_assigned"))
    op.add_column("goals", sa.Column("submission_notes", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("manager_comment", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("ai_assessment", sa.JSON(), nullable=True))
    op.add_column("goals", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("edit_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("last_action_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_goals_last_action_by_users", "goals", "users", ["last_action_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_goals_last_action_by", "goals", ["last_action_by"])
    op.create_index("ix_goals_source_type", "goals", ["source_type"])

    op.create_table(
        "goal_approval_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("from_status", sa.String(length=40), nullable=True),
        sa.Column("to_status", sa.String(length=40), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("ai_assessment", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_goal_approval_history_goal_id", "goal_approval_history", ["goal_id"])
    op.create_index("ix_goal_approval_history_actor_id", "goal_approval_history", ["actor_id"])
    op.create_index("ix_goal_approval_history_action", "goal_approval_history", ["action"])

    op.execute(
        sa.text(
            "UPDATE goals SET source_type = 'self_created' WHERE assigned_by IS NULL AND user_id = assigned_to"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_goal_approval_history_action", table_name="goal_approval_history")
    op.drop_index("ix_goal_approval_history_actor_id", table_name="goal_approval_history")
    op.drop_index("ix_goal_approval_history_goal_id", table_name="goal_approval_history")
    op.drop_table("goal_approval_history")

    op.drop_index("ix_goals_source_type", table_name="goals")
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
