"""extend goal status workflow

Revision ID: 20260411_0007
Revises: 20260411_0006
Create Date: 2026-04-11
"""

from alembic import op

revision = "20260411_0007"
down_revision = "20260411_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE goal_status ADD VALUE IF NOT EXISTS 'edit_requested'")
    op.execute("ALTER TYPE goal_status ADD VALUE IF NOT EXISTS 'withdrawn'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass