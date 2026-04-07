"""prd coach core extensions

Revision ID: 20260331_0023
Revises: 20260330_0022
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260331_0023"
down_revision = "20260330_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("selected_framework", sa.String(), nullable=False, server_default="OKR"))
    op.add_column("employees", sa.Column("cycle_type", sa.String(), nullable=False, server_default="quarterly"))

    op.add_column("goals", sa.Column("approval_deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column("goals", sa.Column("auto_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("goals", sa.Column("drift_flags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")))

    op.add_column("checkins", sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("checkins", sa.Column("quarter", sa.Integer(), nullable=True))
    op.add_column("checkins", sa.Column("year", sa.Integer(), nullable=True))
    op.add_column("checkins", sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("checkins", sa.Column("goal_rag_statuses", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("checkins", sa.Column("ai_agenda", sa.Text(), nullable=True))
    op.add_column("checkins", sa.Column("overall_confidence", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_checkins_overall_confidence_range",
        "checkins",
        "overall_confidence IS NULL OR (overall_confidence >= 1 AND overall_confidence <= 5)",
    )

    op.add_column("meetings", sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("ai_action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("meetings", sa.Column("goal_discussion_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))

    op.create_table(
        "cycle_timeline",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["cycle_id"], ["performance_cycles.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cycle_timeline_employee_id", "cycle_timeline", ["employee_id"])
    op.create_index("ix_cycle_timeline_cycle_id", "cycle_timeline", ["cycle_id"])

    op.create_table(
        "notifications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "email_logs",
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("template_name", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_recipient_id", "email_logs", ["recipient_id"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_recipient_id", table_name="email_logs")
    op.drop_table("email_logs")

    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_cycle_timeline_cycle_id", table_name="cycle_timeline")
    op.drop_index("ix_cycle_timeline_employee_id", table_name="cycle_timeline")
    op.drop_table("cycle_timeline")

    op.drop_column("meetings", "goal_discussion_notes")
    op.drop_column("meetings", "ai_action_items")
    op.drop_column("meetings", "ai_summary")
    op.drop_column("meetings", "transcript")

    op.drop_constraint("ck_checkins_overall_confidence_range", "checkins", type_="check")
    op.drop_column("checkins", "overall_confidence")
    op.drop_column("checkins", "ai_agenda")
    op.drop_column("checkins", "goal_rag_statuses")
    op.drop_column("checkins", "attachments")
    op.drop_column("checkins", "year")
    op.drop_column("checkins", "quarter")
    op.drop_column("checkins", "is_final")

    op.drop_column("goals", "drift_flags")
    op.drop_column("goals", "auto_approved")
    op.drop_column("goals", "approval_deadline")

    op.drop_column("employees", "cycle_type")
    op.drop_column("employees", "selected_framework")
