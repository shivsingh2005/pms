"""framework selection and goal source tables

Revision ID: 20260330_0021
Revises: 20260330_0020
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_0021"
down_revision = "20260330_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_framework_selections",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_framework", sa.String(), nullable=False),
        sa.Column("cycle_type", sa.String(), nullable=False, server_default="quarterly"),
        sa.Column("recommendation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_framework_selections_user_id", "user_framework_selections", ["user_id"])
    op.create_index("ix_user_framework_selections_organization_id", "user_framework_selections", ["organization_id"])

    op.create_table(
        "department_framework_policies",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("allowed_frameworks", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("ARRAY['OKR','MBO','Balanced Scorecard','Competency-Based','Hybrid']::varchar[]")),
        sa.Column("cycle_type", sa.String(), nullable=False, server_default="quarterly"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "department", name="uq_department_framework_policies_org_department"),
    )
    op.create_index("ix_department_framework_policies_organization_id", "department_framework_policies", ["organization_id"])
    op.create_index("ix_department_framework_policies_department", "department_framework_policies", ["department"])

    op.create_table(
        "kpi_library",
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("goal_title", sa.String(), nullable=False),
        sa.Column("goal_description", sa.Text(), nullable=False),
        sa.Column("suggested_kpi", sa.Text(), nullable=False),
        sa.Column("suggested_weight", sa.Float(), nullable=False),
        sa.Column("framework", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kpi_library_role", "kpi_library", ["role"])
    op.create_index("ix_kpi_library_domain", "kpi_library", ["domain"])
    op.create_index("ix_kpi_library_department", "kpi_library", ["department"])
    op.create_index("ix_kpi_library_framework", "kpi_library", ["framework"])

    op.create_table(
        "annual_operating_plan",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("target_value", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_annual_operating_plan_organization_id", "annual_operating_plan", ["organization_id"])
    op.create_index("ix_annual_operating_plan_year", "annual_operating_plan", ["year"])
    op.create_index("ix_annual_operating_plan_department", "annual_operating_plan", ["department"])
    op.create_index("ix_annual_operating_plan_created_by", "annual_operating_plan", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_annual_operating_plan_created_by", table_name="annual_operating_plan")
    op.drop_index("ix_annual_operating_plan_department", table_name="annual_operating_plan")
    op.drop_index("ix_annual_operating_plan_year", table_name="annual_operating_plan")
    op.drop_index("ix_annual_operating_plan_organization_id", table_name="annual_operating_plan")
    op.drop_table("annual_operating_plan")

    op.drop_index("ix_kpi_library_framework", table_name="kpi_library")
    op.drop_index("ix_kpi_library_department", table_name="kpi_library")
    op.drop_index("ix_kpi_library_domain", table_name="kpi_library")
    op.drop_index("ix_kpi_library_role", table_name="kpi_library")
    op.drop_table("kpi_library")

    op.drop_index("ix_department_framework_policies_department", table_name="department_framework_policies")
    op.drop_index("ix_department_framework_policies_organization_id", table_name="department_framework_policies")
    op.drop_table("department_framework_policies")

    op.drop_index("ix_user_framework_selections_organization_id", table_name="user_framework_selections")
    op.drop_index("ix_user_framework_selections_user_id", table_name="user_framework_selections")
    op.drop_table("user_framework_selections")
