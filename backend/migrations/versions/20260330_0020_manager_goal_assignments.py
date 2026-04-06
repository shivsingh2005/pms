"""manager goal assignment table

Revision ID: 20260330_0020
Revises: 20260330_0019
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_0020"
down_revision = "20260330_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goal_assignments",
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_key", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="assigned"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_assignments_goal_id", "goal_assignments", ["goal_id"])
    op.create_index("ix_goal_assignments_employee_id", "goal_assignments", ["employee_id"])
    op.create_index("ix_goal_assignments_manager_id", "goal_assignments", ["manager_id"])
    op.create_index("ix_goal_assignments_role_key", "goal_assignments", ["role_key"])
    op.create_index("ix_goal_assignments_status", "goal_assignments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_goal_assignments_status", table_name="goal_assignments")
    op.drop_index("ix_goal_assignments_role_key", table_name="goal_assignments")
    op.drop_index("ix_goal_assignments_manager_id", table_name="goal_assignments")
    op.drop_index("ix_goal_assignments_employee_id", table_name="goal_assignments")
    op.drop_index("ix_goal_assignments_goal_id", table_name="goal_assignments")
    op.drop_table("goal_assignments")
