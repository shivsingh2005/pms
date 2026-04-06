"""leadership goals and cascade chain foundation

Revision ID: 20260331_0025
Revises: 20260331_0024
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260331_0025"
down_revision = "20260331_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("annual_operating_plan", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("quarter", sa.Integer(), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("total_target_value", sa.Numeric(15, 2), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("target_unit", sa.String(length=50), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("target_metric", sa.Text(), nullable=True))
    op.add_column("annual_operating_plan", sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))
    op.create_foreign_key("fk_aop_cycle_id", "annual_operating_plan", "performance_cycles", ["cycle_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_annual_operating_plan_cycle_id", "annual_operating_plan", ["cycle_id"])
    op.create_index("ix_annual_operating_plan_quarter", "annual_operating_plan", ["quarter"])

    op.create_table(
        "aop_manager_assignments",
        sa.Column("aop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_target_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("assigned_percentage", sa.Float(), nullable=False),
        sa.Column("target_unit", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["aop_id"], ["annual_operating_plan.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aop_manager_assignments_aop_id", "aop_manager_assignments", ["aop_id"])
    op.create_index("ix_aop_manager_assignments_manager_id", "aop_manager_assignments", ["manager_id"])
    op.create_index("ix_aop_manager_assignments_created_by", "aop_manager_assignments", ["created_by"])

    op.add_column("goals", sa.Column("aop_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goals", sa.Column("aop_assignment_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goals", sa.Column("is_cascaded_from_leadership", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("goals", sa.Column("leadership_target_value", sa.Float(), nullable=True))
    op.add_column("goals", sa.Column("leadership_target_unit", sa.String(length=50), nullable=True))
    op.add_column("goals", sa.Column("cascade_source", sa.String(length=20), nullable=True))
    op.create_foreign_key("fk_goals_aop_id", "goals", "annual_operating_plan", ["aop_id"], ["id"])
    op.create_foreign_key("fk_goals_aop_assignment_id", "goals", "aop_manager_assignments", ["aop_assignment_id"], ["id"])
    op.create_index("ix_goals_aop_id", "goals", ["aop_id"])
    op.create_index("ix_goals_aop_assignment_id", "goals", ["aop_assignment_id"])

    op.add_column("goal_lineage", sa.Column("employee_goal_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goal_lineage", sa.Column("manager_goal_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goal_lineage", sa.Column("aop_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goal_lineage", sa.Column("aop_assignment_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("goal_lineage", sa.Column("employee_target_value", sa.Float(), nullable=True))
    op.add_column("goal_lineage", sa.Column("employee_target_percentage", sa.Float(), nullable=True))
    op.add_column("goal_lineage", sa.Column("manager_target_value", sa.Float(), nullable=True))
    op.add_column("goal_lineage", sa.Column("aop_total_value", sa.Float(), nullable=True))
    op.add_column("goal_lineage", sa.Column("contribution_level", sa.String(length=10), nullable=True))
    op.add_column("goal_lineage", sa.Column("business_context", sa.Text(), nullable=True))
    op.create_foreign_key("fk_goal_lineage_employee_goal_id", "goal_lineage", "goals", ["employee_goal_id"], ["id"])
    op.create_foreign_key("fk_goal_lineage_manager_goal_id", "goal_lineage", "goals", ["manager_goal_id"], ["id"])
    op.create_foreign_key("fk_goal_lineage_aop_id", "goal_lineage", "annual_operating_plan", ["aop_id"], ["id"])
    op.create_foreign_key("fk_goal_lineage_aop_assignment_id", "goal_lineage", "aop_manager_assignments", ["aop_assignment_id"], ["id"])
    op.create_index("ix_goal_lineage_employee_goal_id", "goal_lineage", ["employee_goal_id"])
    op.create_index("ix_goal_lineage_manager_goal_id", "goal_lineage", ["manager_goal_id"])
    op.create_index("ix_goal_lineage_aop_id", "goal_lineage", ["aop_id"])
    op.create_index("ix_goal_lineage_aop_assignment_id", "goal_lineage", ["aop_assignment_id"])


def downgrade() -> None:
    op.drop_index("ix_goal_lineage_aop_assignment_id", table_name="goal_lineage")
    op.drop_index("ix_goal_lineage_aop_id", table_name="goal_lineage")
    op.drop_index("ix_goal_lineage_manager_goal_id", table_name="goal_lineage")
    op.drop_index("ix_goal_lineage_employee_goal_id", table_name="goal_lineage")
    op.drop_constraint("fk_goal_lineage_aop_assignment_id", "goal_lineage", type_="foreignkey")
    op.drop_constraint("fk_goal_lineage_aop_id", "goal_lineage", type_="foreignkey")
    op.drop_constraint("fk_goal_lineage_manager_goal_id", "goal_lineage", type_="foreignkey")
    op.drop_constraint("fk_goal_lineage_employee_goal_id", "goal_lineage", type_="foreignkey")
    op.drop_column("goal_lineage", "business_context")
    op.drop_column("goal_lineage", "contribution_level")
    op.drop_column("goal_lineage", "aop_total_value")
    op.drop_column("goal_lineage", "manager_target_value")
    op.drop_column("goal_lineage", "employee_target_percentage")
    op.drop_column("goal_lineage", "employee_target_value")
    op.drop_column("goal_lineage", "aop_assignment_id")
    op.drop_column("goal_lineage", "aop_id")
    op.drop_column("goal_lineage", "manager_goal_id")
    op.drop_column("goal_lineage", "employee_goal_id")

    op.drop_index("ix_goals_aop_assignment_id", table_name="goals")
    op.drop_index("ix_goals_aop_id", table_name="goals")
    op.drop_constraint("fk_goals_aop_assignment_id", "goals", type_="foreignkey")
    op.drop_constraint("fk_goals_aop_id", "goals", type_="foreignkey")
    op.drop_column("goals", "cascade_source")
    op.drop_column("goals", "leadership_target_unit")
    op.drop_column("goals", "leadership_target_value")
    op.drop_column("goals", "is_cascaded_from_leadership")
    op.drop_column("goals", "aop_assignment_id")
    op.drop_column("goals", "aop_id")

    op.drop_index("ix_aop_manager_assignments_created_by", table_name="aop_manager_assignments")
    op.drop_index("ix_aop_manager_assignments_manager_id", table_name="aop_manager_assignments")
    op.drop_index("ix_aop_manager_assignments_aop_id", table_name="aop_manager_assignments")
    op.drop_table("aop_manager_assignments")

    op.drop_index("ix_annual_operating_plan_quarter", table_name="annual_operating_plan")
    op.drop_index("ix_annual_operating_plan_cycle_id", table_name="annual_operating_plan")
    op.drop_constraint("fk_aop_cycle_id", "annual_operating_plan", type_="foreignkey")
    op.drop_column("annual_operating_plan", "status")
    op.drop_column("annual_operating_plan", "target_metric")
    op.drop_column("annual_operating_plan", "target_unit")
    op.drop_column("annual_operating_plan", "total_target_value")
    op.drop_column("annual_operating_plan", "quarter")
    op.drop_column("annual_operating_plan", "description")
    op.drop_column("annual_operating_plan", "title")
    op.drop_column("annual_operating_plan", "cycle_id")
