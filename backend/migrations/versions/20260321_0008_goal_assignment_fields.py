"""add goal assignment metadata fields

Revision ID: 20260321_0008
Revises: 20260321_0007
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260321_0008"
down_revision = "20260321_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("goals", sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goals", sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goals", sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    op.create_foreign_key("fk_goals_assigned_by_users", "goals", "users", ["assigned_by"], ["id"])
    op.create_foreign_key("fk_goals_assigned_to_users", "goals", "users", ["assigned_to"], ["id"])
    op.create_index("ix_goals_assigned_by", "goals", ["assigned_by"])
    op.create_index("ix_goals_assigned_to", "goals", ["assigned_to"])

    op.execute("UPDATE goals SET assigned_to = user_id WHERE assigned_to IS NULL")


def downgrade() -> None:
    op.drop_index("ix_goals_assigned_to", table_name="goals")
    op.drop_index("ix_goals_assigned_by", table_name="goals")
    op.drop_constraint("fk_goals_assigned_to_users", "goals", type_="foreignkey")
    op.drop_constraint("fk_goals_assigned_by_users", "goals", type_="foreignkey")
    op.drop_column("goals", "is_ai_generated")
    op.drop_column("goals", "assigned_to")
    op.drop_column("goals", "assigned_by")
