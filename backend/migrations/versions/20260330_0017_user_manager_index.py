"""add users.manager_id index

Revision ID: 20260330_0017
Revises: 20260329_0016
Create Date: 2026-03-30
"""

from alembic import op

revision = "20260330_0017"
down_revision = "20260329_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_users_manager_id", "users", ["manager_id"])


def downgrade() -> None:
    op.drop_index("ix_users_manager_id", table_name="users")
