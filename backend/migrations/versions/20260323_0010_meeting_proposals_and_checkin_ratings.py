"""meeting proposals and checkin ratings workflow

Revision ID: 20260323_0010
Revises: 20260322_0009
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260323_0010"
down_revision = "20260322_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    proposal_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="meeting_proposal_status",
        create_type=False,
    )
    bind = op.get_bind()
    proposal_status.create(bind, checkfirst=True)

    op.create_table(
        "meeting_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("checkin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("checkins.id"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("proposed_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", proposal_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_meeting_proposals_checkin_id", "meeting_proposals", ["checkin_id"])
    op.create_index("ix_meeting_proposals_employee_id", "meeting_proposals", ["employee_id"])
    op.create_index("ix_meeting_proposals_manager_id", "meeting_proposals", ["manager_id"])
    op.create_index("ix_meeting_proposals_status", "meeting_proposals", ["status"])

    op.create_table(
        "checkin_ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("checkin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("checkins.id"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_checkin_ratings_range"),
    )
    op.create_index("ix_checkin_ratings_checkin_id", "checkin_ratings", ["checkin_id"])
    op.create_index("ix_checkin_ratings_employee_id", "checkin_ratings", ["employee_id"])
    op.create_index("ix_checkin_ratings_manager_id", "checkin_ratings", ["manager_id"])

    op.add_column("meetings", sa.Column("checkin_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("meetings", sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("meetings", sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("meetings", sa.Column("meet_link", sa.String(), nullable=True))

    op.create_foreign_key("fk_meetings_checkin_id", "meetings", "checkins", ["checkin_id"], ["id"])
    op.create_foreign_key("fk_meetings_employee_id", "meetings", "users", ["employee_id"], ["id"])
    op.create_foreign_key("fk_meetings_manager_id", "meetings", "users", ["manager_id"], ["id"])

    op.create_index("ix_meetings_checkin_id", "meetings", ["checkin_id"])
    op.create_index("ix_meetings_employee_id", "meetings", ["employee_id"])
    op.create_index("ix_meetings_manager_id", "meetings", ["manager_id"])

    op.execute(
        """
        UPDATE meetings
        SET meet_link = google_meet_link
        WHERE meet_link IS NULL AND google_meet_link IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE meetings m
        SET employee_id = g.user_id
        FROM goals g
        WHERE m.goal_id = g.id AND m.employee_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE meetings m
        SET manager_id = u.manager_id
        FROM users u
        WHERE m.employee_id = u.id AND m.manager_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_meetings_manager_id", table_name="meetings")
    op.drop_index("ix_meetings_employee_id", table_name="meetings")
    op.drop_index("ix_meetings_checkin_id", table_name="meetings")

    op.drop_constraint("fk_meetings_manager_id", "meetings", type_="foreignkey")
    op.drop_constraint("fk_meetings_employee_id", "meetings", type_="foreignkey")
    op.drop_constraint("fk_meetings_checkin_id", "meetings", type_="foreignkey")

    op.drop_column("meetings", "meet_link")
    op.drop_column("meetings", "manager_id")
    op.drop_column("meetings", "employee_id")
    op.drop_column("meetings", "checkin_id")

    op.drop_index("ix_checkin_ratings_manager_id", table_name="checkin_ratings")
    op.drop_index("ix_checkin_ratings_employee_id", table_name="checkin_ratings")
    op.drop_index("ix_checkin_ratings_checkin_id", table_name="checkin_ratings")
    op.drop_table("checkin_ratings")

    op.drop_index("ix_meeting_proposals_status", table_name="meeting_proposals")
    op.drop_index("ix_meeting_proposals_manager_id", table_name="meeting_proposals")
    op.drop_index("ix_meeting_proposals_employee_id", table_name="meeting_proposals")
    op.drop_index("ix_meeting_proposals_checkin_id", table_name="meeting_proposals")
    op.drop_table("meeting_proposals")

    bind = op.get_bind()
    sa.Enum(name="meeting_proposal_status").drop(bind, checkfirst=True)
