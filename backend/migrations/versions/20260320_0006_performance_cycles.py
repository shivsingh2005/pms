"""add performance cycles table

Revision ID: 20260320_0006
Revises: 20260320_0005
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260320_0006"
down_revision = "20260320_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("cycle_type", sa.String(), nullable=False),
        sa.Column("framework", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("goal_setting_deadline", sa.Date(), nullable=False),
        sa.Column("self_review_deadline", sa.Date(), nullable=False),
        sa.Column("checkin_cap_per_quarter", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("ai_usage_cap_per_quarter", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_performance_cycles_organization_id", "performance_cycles", ["organization_id"])
    op.create_index("ix_performance_cycles_is_active", "performance_cycles", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_performance_cycles_is_active", table_name="performance_cycles")
    op.drop_index("ix_performance_cycles_organization_id", table_name="performance_cycles")
    op.drop_table("performance_cycles")
