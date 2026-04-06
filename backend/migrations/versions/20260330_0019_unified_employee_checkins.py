"""unify checkins as employee-level records

Revision ID: 20260330_0019
Revises: 20260330_0018
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_0019"
down_revision = "20260330_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("checkins", sa.Column("goal_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True))
    op.add_column(
        "checkins",
        sa.Column("goal_updates", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column("checkins", sa.Column("overall_progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("checkins", sa.Column("achievements", sa.Text(), nullable=True))
    op.add_column("checkins", sa.Column("confidence_level", sa.Integer(), nullable=True))

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
        WITH ranked AS (
            SELECT
                c.id,
                c.employee_id,
                c.cycle_id,
                first_value(c.id) OVER (
                    PARTITION BY c.employee_id, c.cycle_id
                    ORDER BY c.created_at DESC, c.id DESC
                ) AS keeper_id
            FROM checkins c
            WHERE c.cycle_id IS NOT NULL
        ),
        dupes AS (
            SELECT id, keeper_id
            FROM ranked
            WHERE id <> keeper_id
        )
        UPDATE meeting_proposals mp
        SET checkin_id = d.keeper_id
        FROM dupes d
        WHERE mp.checkin_id = d.id
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                c.id,
                c.employee_id,
                c.cycle_id,
                first_value(c.id) OVER (
                    PARTITION BY c.employee_id, c.cycle_id
                    ORDER BY c.created_at DESC, c.id DESC
                ) AS keeper_id
            FROM checkins c
            WHERE c.cycle_id IS NOT NULL
        ),
        dupes AS (
            SELECT id, keeper_id
            FROM ranked
            WHERE id <> keeper_id
        )
        UPDATE checkin_ratings cr
        SET checkin_id = d.keeper_id
        FROM dupes d
        WHERE cr.checkin_id = d.id
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                c.id,
                c.employee_id,
                c.cycle_id,
                first_value(c.id) OVER (
                    PARTITION BY c.employee_id, c.cycle_id
                    ORDER BY c.created_at DESC, c.id DESC
                ) AS keeper_id
            FROM checkins c
            WHERE c.cycle_id IS NOT NULL
        ),
        dupes AS (
            SELECT id, keeper_id
            FROM ranked
            WHERE id <> keeper_id
        )
        UPDATE meetings m
        SET checkin_id = d.keeper_id
        FROM dupes d
        WHERE m.checkin_id = d.id
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                c.id,
                c.employee_id,
                c.cycle_id,
                first_value(c.id) OVER (
                    PARTITION BY c.employee_id, c.cycle_id
                    ORDER BY c.created_at DESC, c.id DESC
                ) AS keeper_id
            FROM checkins c
            WHERE c.cycle_id IS NOT NULL
        ),
        grouped AS (
            SELECT
                r.keeper_id,
                array_remove(array_agg(DISTINCT c.goal_id), NULL) AS merged_goal_ids,
                ROUND(AVG(COALESCE(c.progress, 0)))::int AS merged_progress,
                string_agg(DISTINCT NULLIF(trim(c.summary), ''), E'\n---\n') AS merged_summary,
                string_agg(DISTINCT NULLIF(trim(c.blockers), ''), E'\n') AS merged_blockers,
                string_agg(DISTINCT NULLIF(trim(c.next_steps), ''), E'\n') AS merged_achievements,
                jsonb_agg(
                    jsonb_build_object(
                        'goal_id', c.goal_id::text,
                        'progress', COALESCE(c.progress, 0),
                        'note', NULL
                    )
                ) FILTER (WHERE c.goal_id IS NOT NULL) AS merged_goal_updates
            FROM checkins c
            JOIN ranked r ON r.id = c.id
            GROUP BY r.keeper_id
        )
        UPDATE checkins k
        SET
            goal_ids = COALESCE(g.merged_goal_ids, ARRAY[]::uuid[]),
            goal_updates = COALESCE(g.merged_goal_updates, '[]'::jsonb),
            overall_progress = COALESCE(g.merged_progress, 0),
            summary = COALESCE(NULLIF(g.merged_summary, ''), COALESCE(k.summary, 'Legacy check-in')),
            blockers = COALESCE(g.merged_blockers, k.blockers),
            achievements = COALESCE(g.merged_achievements, k.next_steps)
        FROM grouped g
        WHERE k.id = g.keeper_id
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                c.id,
                c.employee_id,
                c.cycle_id,
                first_value(c.id) OVER (
                    PARTITION BY c.employee_id, c.cycle_id
                    ORDER BY c.created_at DESC, c.id DESC
                ) AS keeper_id
            FROM checkins c
            WHERE c.cycle_id IS NOT NULL
        ),
        dupes AS (
            SELECT id
            FROM ranked
            WHERE id <> keeper_id
        )
        DELETE FROM checkins c
        USING dupes d
        WHERE c.id = d.id
        """
    )

    op.execute("UPDATE checkins SET goal_ids = ARRAY[goal_id] WHERE goal_ids IS NULL AND goal_id IS NOT NULL")
    op.execute("UPDATE checkins SET goal_ids = ARRAY[]::uuid[] WHERE goal_ids IS NULL")
    op.execute("UPDATE checkins SET overall_progress = COALESCE(progress, 0)")
    op.execute("UPDATE checkins SET achievements = COALESCE(achievements, next_steps)")
    op.execute("UPDATE checkins SET summary = COALESCE(summary, 'Legacy check-in')")

    op.alter_column("checkins", "goal_ids", nullable=False)
    op.alter_column("checkins", "summary", nullable=False)

    op.drop_constraint("ck_checkins_progress_range", "checkins", type_="check")
    op.create_check_constraint(
        "ck_checkins_overall_progress_range",
        "checkins",
        "overall_progress >= 0 AND overall_progress <= 100",
    )
    op.create_check_constraint(
        "ck_checkins_confidence_range",
        "checkins",
        "confidence_level IS NULL OR (confidence_level >= 1 AND confidence_level <= 5)",
    )

    op.create_index(
        "ux_checkins_employee_cycle",
        "checkins",
        ["employee_id", "cycle_id"],
        unique=True,
        postgresql_where=sa.text("cycle_id IS NOT NULL"),
    )

    op.execute("UPDATE meetings SET goal_id = NULL WHERE meeting_type = 'CHECKIN' AND checkin_id IS NOT NULL")

    op.drop_column("checkins", "goal_id")
    op.drop_column("checkins", "progress")
    op.drop_column("checkins", "next_steps")

    op.alter_column("checkins", "goal_updates", server_default=None)
    op.alter_column("checkins", "overall_progress", server_default=None)


def downgrade() -> None:
    op.add_column("checkins", sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("checkins", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("checkins", sa.Column("next_steps", sa.Text(), nullable=True))

    op.execute("UPDATE checkins SET goal_id = goal_ids[1] WHERE cardinality(goal_ids) > 0")
    op.execute("UPDATE checkins SET progress = COALESCE(overall_progress, 0)")
    op.execute("UPDATE checkins SET next_steps = achievements")

    op.drop_index("ux_checkins_employee_cycle", table_name="checkins")
    op.drop_constraint("ck_checkins_confidence_range", "checkins", type_="check")
    op.drop_constraint("ck_checkins_overall_progress_range", "checkins", type_="check")
    op.create_check_constraint("ck_checkins_progress_range", "checkins", "progress >= 0 AND progress <= 100")

    op.drop_column("checkins", "confidence_level")
    op.drop_column("checkins", "achievements")
    op.drop_column("checkins", "overall_progress")
    op.drop_column("checkins", "goal_updates")
    op.drop_column("checkins", "goal_ids")

    op.alter_column("checkins", "progress", server_default=None)
