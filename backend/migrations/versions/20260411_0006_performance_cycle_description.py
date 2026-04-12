"""add performance cycle description

Revision ID: 20260411_0006
Revises: 20260407_0005
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa

revision = "20260411_0006"
down_revision = "20260407_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("performance_cycles", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("performance_cycles", "description")