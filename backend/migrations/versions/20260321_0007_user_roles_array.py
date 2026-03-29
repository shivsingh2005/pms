"""add roles array to users

Revision ID: 20260321_0007
Revises: 20260320_0006
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260321_0007"
down_revision = "20260320_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=True))

    op.execute(
        """
        UPDATE users
        SET roles = CASE
            WHEN role::text = 'manager' THEN ARRAY['employee', 'manager']::text[]
            ELSE ARRAY[role::text]
        END
        WHERE roles IS NULL;
        """
    )


def downgrade() -> None:
    op.drop_column("users", "roles")
