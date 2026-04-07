"""goal phase2 lineage and change logs

Revision ID: 20260330_0022
Revises: 20260330_0021
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_0022"
down_revision = "20260330_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goal_lineage",
        sa.Column("parent_goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contribution_percentage", sa.Float(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_goal_id", "child_goal_id", name="uq_goal_lineage_parent_child"),
    )
    op.create_index("ix_goal_lineage_parent_goal_id", "goal_lineage", ["parent_goal_id"])
    op.create_index("ix_goal_lineage_child_goal_id", "goal_lineage", ["child_goal_id"])
    op.create_index("ix_goal_lineage_created_by", "goal_lineage", ["created_by"])

    op.create_table(
        "goal_change_logs",
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_change_logs_goal_id", "goal_change_logs", ["goal_id"])
    op.create_index("ix_goal_change_logs_changed_by", "goal_change_logs", ["changed_by"])
    op.create_index("ix_goal_change_logs_change_type", "goal_change_logs", ["change_type"])


def downgrade() -> None:
    op.drop_index("ix_goal_change_logs_change_type", table_name="goal_change_logs")
    op.drop_index("ix_goal_change_logs_changed_by", table_name="goal_change_logs")
    op.drop_index("ix_goal_change_logs_goal_id", table_name="goal_change_logs")
    op.drop_table("goal_change_logs")

    op.drop_index("ix_goal_lineage_created_by", table_name="goal_lineage")
    op.drop_index("ix_goal_lineage_child_goal_id", table_name="goal_lineage")
    op.drop_index("ix_goal_lineage_parent_goal_id", table_name="goal_lineage")
    op.drop_table("goal_lineage")
