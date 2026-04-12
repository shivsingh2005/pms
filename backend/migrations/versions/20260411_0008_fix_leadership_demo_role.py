"""fix leadership demo role

Revision ID: 20260411_0008
Revises: 20260411_0007_extend_goal_status_enum
Create Date: 2026-04-11
"""

from alembic import op

revision = "20260411_0008"
down_revision = "20260411_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET role = 'leadership', roles = ARRAY['leadership']::varchar[]
        WHERE lower(email) = 'leadership@structured.mock'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET role = 'manager', roles = ARRAY['manager', 'employee']::varchar[]
        WHERE lower(email) = 'leadership@structured.mock'
        """
    )