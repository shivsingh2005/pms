"""remove admin role and admin portal tables

Revision ID: 20260330_0018
Revises: 20260330_0017
Create Date: 2026-03-30
"""

from alembic import op

revision = "20260330_0018"
down_revision = "20260330_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Migrate any legacy admin users before removing enum value.
    op.execute("UPDATE users SET role = 'hr' WHERE role::text = 'admin'")
    op.execute("UPDATE employees SET role = 'hr' WHERE role::text = 'admin'")
    op.execute(
        """
        UPDATE users
        SET roles = ARRAY(
            SELECT DISTINCT value
            FROM unnest(array_replace(roles, 'admin', 'hr')) AS value
            WHERE value <> 'admin'
        )
        WHERE roles IS NOT NULL
        """
    )

    # Remove deprecated admin portal tables.
    op.execute("DROP TABLE IF EXISTS admin_audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS admin_system_settings CASCADE")
    op.execute("DROP TABLE IF EXISTS admin_role_permissions CASCADE")

    # Rebuild enum type without the admin role.
    op.execute("CREATE TYPE user_role_new AS ENUM ('employee', 'manager', 'hr', 'leadership')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role_new USING role::text::user_role_new")
    op.execute("ALTER TABLE employees ALTER COLUMN role TYPE user_role_new USING role::text::user_role_new")
    op.execute("DROP TYPE user_role")
    op.execute("ALTER TYPE user_role_new RENAME TO user_role")


def downgrade() -> None:
    op.execute("CREATE TYPE user_role_old AS ENUM ('employee', 'manager', 'hr', 'leadership', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role_old USING role::text::user_role_old")
    op.execute("ALTER TABLE employees ALTER COLUMN role TYPE user_role_old USING role::text::user_role_old")
    op.execute("DROP TYPE user_role")
    op.execute("ALTER TYPE user_role_old RENAME TO user_role")
