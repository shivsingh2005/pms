"""add cycle lifecycle status and bind performance entities to cycles

Revision ID: 20260329_0016
Revises: 20260328_0015
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260329_0016"
down_revision = "20260328_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cycle_status_enum = sa.Enum("planning", "active", "closed", "locked", name="performance_cycle_status")
    cycle_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "performance_cycles",
        sa.Column("status", cycle_status_enum, nullable=False, server_default=sa.text("'planning'")),
    )
    op.add_column("performance_cycles", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_performance_cycles_status", "performance_cycles", ["status"])

    op.execute("UPDATE performance_cycles SET status = 'active' WHERE is_active = true")
    op.alter_column("performance_cycles", "status", server_default=None)

    op.add_column("goals", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_goals_cycle_id", "goals", ["cycle_id"])
    op.create_foreign_key("fk_goals_cycle_id", "goals", "performance_cycles", ["cycle_id"], ["id"])

    op.add_column("checkins", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_checkins_cycle_id", "checkins", ["cycle_id"])
    op.create_foreign_key("fk_checkins_cycle_id", "checkins", "performance_cycles", ["cycle_id"], ["id"])

    op.add_column("meetings", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_meetings_cycle_id", "meetings", ["cycle_id"])
    op.create_foreign_key("fk_meetings_cycle_id", "meetings", "performance_cycles", ["cycle_id"], ["id"])

    op.add_column("ratings", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_ratings_cycle_id", "ratings", ["cycle_id"])
    op.create_foreign_key("fk_ratings_cycle_id", "ratings", "performance_cycles", ["cycle_id"], ["id"])

    op.add_column("checkin_ratings", sa.Column("cycle_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_checkin_ratings_cycle_id", "checkin_ratings", ["cycle_id"])
    op.create_foreign_key("fk_checkin_ratings_cycle_id", "checkin_ratings", "performance_cycles", ["cycle_id"], ["id"])

    op.execute(
        """
        UPDATE goals g
        SET cycle_id = pc.id
        FROM users u
        JOIN performance_cycles pc ON pc.organization_id = u.organization_id
        WHERE g.user_id = u.id
          AND g.cycle_id IS NULL
          AND pc.is_active = true
          AND pc.start_date = (
              SELECT max(pc2.start_date)
              FROM performance_cycles pc2
              WHERE pc2.organization_id = u.organization_id
                AND pc2.is_active = true
          )
        """
    )

    op.execute(
        """
        UPDATE checkins c
        SET cycle_id = g.cycle_id
        FROM goals g
        WHERE c.goal_id = g.id
          AND c.cycle_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE meetings m
        SET cycle_id = g.cycle_id
        FROM goals g
        WHERE m.goal_id = g.id
          AND m.cycle_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE meetings m
        SET cycle_id = c.cycle_id
        FROM checkins c
        WHERE m.checkin_id = c.id
          AND m.cycle_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE ratings r
        SET cycle_id = g.cycle_id
        FROM goals g
        WHERE r.goal_id = g.id
          AND r.cycle_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE checkin_ratings cr
        SET cycle_id = c.cycle_id
        FROM checkins c
        WHERE cr.checkin_id = c.id
          AND cr.cycle_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_checkin_ratings_cycle_id", "checkin_ratings", type_="foreignkey")
    op.drop_index("ix_checkin_ratings_cycle_id", table_name="checkin_ratings")
    op.drop_column("checkin_ratings", "cycle_id")

    op.drop_constraint("fk_ratings_cycle_id", "ratings", type_="foreignkey")
    op.drop_index("ix_ratings_cycle_id", table_name="ratings")
    op.drop_column("ratings", "cycle_id")

    op.drop_constraint("fk_meetings_cycle_id", "meetings", type_="foreignkey")
    op.drop_index("ix_meetings_cycle_id", table_name="meetings")
    op.drop_column("meetings", "cycle_id")

    op.drop_constraint("fk_checkins_cycle_id", "checkins", type_="foreignkey")
    op.drop_index("ix_checkins_cycle_id", table_name="checkins")
    op.drop_column("checkins", "cycle_id")

    op.drop_constraint("fk_goals_cycle_id", "goals", type_="foreignkey")
    op.drop_index("ix_goals_cycle_id", table_name="goals")
    op.drop_column("goals", "cycle_id")

    op.drop_index("ix_performance_cycles_status", table_name="performance_cycles")
    op.drop_column("performance_cycles", "locked_at")
    op.drop_column("performance_cycles", "status")

    bind = op.get_bind()
    cycle_status_enum = sa.Enum("planning", "active", "closed", "locked", name="performance_cycle_status")
    cycle_status_enum.drop(bind, checkfirst=True)
