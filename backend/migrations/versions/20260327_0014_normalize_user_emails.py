"""normalize user emails to lowercase and trimmed values

Revision ID: 20260327_0014
Revises: 20260325_0013
Create Date: 2026-03-27
"""

from alembic import op

revision = "20260327_0014"
down_revision = "20260325_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET email = LOWER(BTRIM(email))
        WHERE email IS NOT NULL
          AND email <> LOWER(BTRIM(email));
        """
    )


def downgrade() -> None:
    # Irreversible normalization; keep as no-op.
    pass
