"""add google access token column to users

Revision ID: 20260328_0015
Revises: 20260327_0014
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa

revision = "20260328_0015"
down_revision = "20260327_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_access_token", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "google_access_token")
