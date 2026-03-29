"""admin portal tables and soft-delete support

Revision ID: 20260324_0012
Revises: 20260324_0011
Create Date: 2026-03-24
"""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260324_0012"
down_revision = "20260324_0011"
branch_labels = None
depends_on = None


ROLE_SEEDS = [
    {
        "role_key": "admin",
        "display_name": "Admin",
        "permissions": [
            "users:create",
            "users:update",
            "users:delete",
            "users:assign_manager",
            "users:assign_role",
            "roles:manage",
            "org:view",
            "org:reassign",
            "settings:manage",
            "audit:view",
        ],
        "is_system": True,
    },
    {"role_key": "hr", "display_name": "HR", "permissions": ["users:view", "users:update", "org:view", "reports:view"], "is_system": True},
    {"role_key": "manager", "display_name": "Manager", "permissions": ["goals:create", "checkins:approve", "team:view"], "is_system": True},
    {"role_key": "employee", "display_name": "Employee", "permissions": ["checkins:submit", "goals:view"], "is_system": True},
    {"role_key": "leadership", "display_name": "Leadership", "permissions": ["org:view", "reports:view", "insights:view"], "is_system": True},
]

SETTING_SEEDS = [
    {"key": "working_hours", "value": {"start": "09:00", "end": "18:00", "timezone": "UTC"}},
    {
        "key": "rating_scale",
        "value": {"min": 1, "max": 5, "labels": {"1": "NI", "2": "SME", "3": "ME", "4": "DE", "5": "EE"}},
    },
    {"key": "checkin_frequency", "value": {"mode": "weekly", "days": ["Friday"]}},
    {"key": "ai_settings", "value": {"provider": "gemini", "model": "gemini-2.5-flash", "api_key_masked": ""}},
]


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "admin_role_permissions",
        sa.Column("role_key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("role_key"),
    )

    op.create_table(
        "admin_system_settings",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "admin_audit_logs",
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_admin_audit_logs_actor_user_id"), "admin_audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_action"), "admin_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_target_type"), "admin_audit_logs", ["target_type"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_target_id"), "admin_audit_logs", ["target_id"], unique=False)

    now = datetime.now(timezone.utc)
    role_table = sa.table(
        "admin_role_permissions",
        sa.column("role_key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("permissions", postgresql.JSONB),
        sa.column("is_system", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    settings_table = sa.table(
        "admin_system_settings",
        sa.column("key", sa.String),
        sa.column("value", postgresql.JSONB),
        sa.column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        role_table,
        [
            {
                "role_key": role["role_key"],
                "display_name": role["display_name"],
                "permissions": role["permissions"],
                "is_system": role["is_system"],
                "created_at": now,
                "updated_at": now,
            }
            for role in ROLE_SEEDS
        ],
    )

    op.bulk_insert(
        settings_table,
        [
            {
                "key": setting["key"],
                "value": setting["value"],
                "updated_by": None,
                "updated_at": now,
            }
            for setting in SETTING_SEEDS
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_logs_target_id"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_target_type"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_action"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_actor_user_id"), table_name="admin_audit_logs")

    op.drop_table("admin_audit_logs")
    op.drop_table("admin_system_settings")
    op.drop_table("admin_role_permissions")

    op.drop_column("users", "deleted_at")
