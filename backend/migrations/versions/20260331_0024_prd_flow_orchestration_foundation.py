"""prd flow orchestration foundation

Revision ID: 20260331_0024
Revises: 20260331_0023
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260331_0024"
down_revision = "20260331_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Onboarding/profile context columns
    op.add_column("users", sa.Column("domain", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("business_unit", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("first_login", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("users", sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("last_active", sa.DateTime(timezone=True), nullable=True))

    op.add_column("employees", sa.Column("domain", sa.String(length=100), nullable=True))
    op.add_column("employees", sa.Column("business_unit", sa.String(length=100), nullable=True))
    op.add_column("employees", sa.Column("first_login", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("employees", sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("employees", sa.Column("last_active", sa.DateTime(timezone=True), nullable=True))

    # Remove old unique-one-checkin-per-cycle constraint to support quarterly cap flows.
    op.execute("DROP INDEX IF EXISTS ux_checkins_employee_cycle")

    # Check-in attachments
    op.create_table(
        "checkin_attachments",
        sa.Column("checkin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=10), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["checkin_id"], ["checkins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checkin_attachments_checkin_id", "checkin_attachments", ["checkin_id"])

    # Dual reporting
    op.create_table(
        "employee_manager_mapping",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weight_percentage", sa.Float(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("weight_percentage > 0 AND weight_percentage <= 100", name="ck_employee_manager_weight_range"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "manager_id", name="uq_employee_manager_mapping_employee_manager"),
    )
    op.create_index("ix_employee_manager_mapping_employee_id", "employee_manager_mapping", ["employee_id"])
    op.create_index("ix_employee_manager_mapping_manager_id", "employee_manager_mapping", ["manager_id"])

    # 9-box
    op.create_table(
        "employee_9box",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("performance_axis", sa.String(length=10), nullable=False),
        sa.Column("potential_axis", sa.String(length=10), nullable=False),
        sa.Column("box_label", sa.String(length=30), nullable=False),
        sa.Column("performance_score", sa.Float(), nullable=False),
        sa.Column("potential_score", sa.Float(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["cycle_id"], ["performance_cycles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employee_9box_employee_id", "employee_9box", ["employee_id"])
    op.create_index("ix_employee_9box_cycle_id", "employee_9box", ["cycle_id"])

    # Succession planning
    op.create_table(
        "succession_planning",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_role", sa.String(length=100), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("readiness_level", sa.String(length=20), nullable=False),
        sa.Column("gaps", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("ARRAY[]::text[]")),
        sa.Column("development_plan", sa.Text(), nullable=True),
        sa.Column("nominated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["nominated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_succession_planning_employee_id", "succession_planning", ["employee_id"])
    op.create_index("ix_succession_planning_nominated_by", "succession_planning", ["nominated_by"])


def downgrade() -> None:
    op.drop_index("ix_succession_planning_nominated_by", table_name="succession_planning")
    op.drop_index("ix_succession_planning_employee_id", table_name="succession_planning")
    op.drop_table("succession_planning")

    op.drop_index("ix_employee_9box_cycle_id", table_name="employee_9box")
    op.drop_index("ix_employee_9box_employee_id", table_name="employee_9box")
    op.drop_table("employee_9box")

    op.drop_index("ix_employee_manager_mapping_manager_id", table_name="employee_manager_mapping")
    op.drop_index("ix_employee_manager_mapping_employee_id", table_name="employee_manager_mapping")
    op.drop_table("employee_manager_mapping")

    op.drop_index("ix_checkin_attachments_checkin_id", table_name="checkin_attachments")
    op.drop_table("checkin_attachments")

    op.create_index(
        "ux_checkins_employee_cycle",
        "checkins",
        ["employee_id", "cycle_id"],
        unique=True,
        postgresql_where=sa.text("cycle_id IS NOT NULL"),
    )

    op.drop_column("employees", "last_active")
    op.drop_column("employees", "onboarding_complete")
    op.drop_column("employees", "first_login")
    op.drop_column("employees", "business_unit")
    op.drop_column("employees", "domain")

    op.drop_column("users", "last_active")
    op.drop_column("users", "onboarding_complete")
    op.drop_column("users", "first_login")
    op.drop_column("users", "business_unit")
    op.drop_column("users", "domain")
