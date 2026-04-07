"""add summary column to meetings

Revision ID: 20260324_0011
Revises: 20260323_0010
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

revision = "20260324_0011"
down_revision = "20260323_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "summary")
