"""Add goal_clusters table for universal cluster management

Revision ID: 20260403_0026
Revises: 20260331_0025
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260403_0026"
down_revision = "20260331_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goal_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cluster_name", sa.String(100), nullable=False),
        sa.Column("cluster_category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("applicable_functions", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_clusters_cluster_name", "goal_clusters", ["cluster_name"])
    op.create_index("ix_goal_clusters_cluster_category", "goal_clusters", ["cluster_category"])


def downgrade() -> None:
    op.drop_index("ix_goal_clusters_cluster_category", table_name="goal_clusters")
    op.drop_index("ix_goal_clusters_cluster_name", table_name="goal_clusters")
    op.drop_table("goal_clusters")
