from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import Checkin
from app.models.enums import GoalStatus, MeetingProposalStatus, UserRole
from app.models.goal import Goal
from app.models.meeting_proposal import MeetingProposal
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User


@dataclass
class NextActionPayload:
    title: str
    detail: str
    action_url: str
    action_label: str
    level: str = "info"


class WorkflowService:
    @staticmethod
    async def _active_cycle(user: User, db: AsyncSession) -> PerformanceCycle | None:
        result = await db.execute(
            select(PerformanceCycle)
            .where(
                PerformanceCycle.organization_id == user.organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .order_by(PerformanceCycle.start_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _employee_next_action(user: User, db: AsyncSession) -> NextActionPayload:
        if user.first_login or not user.onboarding_complete:
            return NextActionPayload(
                title="Complete onboarding tour",
                detail="Start the guided role-specific tour to understand your cycle workflow.",
                action_url="/employee/dashboard?tour=1",
                action_label="Start Tour",
            )

        cycle = await WorkflowService._active_cycle(user, db)
        if not cycle:
            return NextActionPayload(
                title="No active cycle",
                detail="Your organization has not activated a performance cycle yet.",
                action_url="/employee/dashboard",
                action_label="Refresh",
                level="warning",
            )

        goals_result = await db.execute(
            select(Goal)
            .where(Goal.user_id == user.id, Goal.cycle_id == cycle.id)
            .order_by(Goal.created_at.asc())
        )
        goals = list(goals_result.scalars().all())

        if not goals:
            return NextActionPayload(
                title="Set your goals",
                detail="Start your performance cycle by creating role-aligned goals.",
                action_url="/goals",
                action_label="Set Goals",
                level="warning",
            )

        pending_submission = sum(1 for goal in goals if goal.status == GoalStatus.draft)
        if pending_submission > 0:
            return NextActionPayload(
                title=f"You have {pending_submission} goals pending submission",
                detail="Submit all goals to unlock manager approval and check-in flow.",
                action_url="/goals",
                action_label="Submit Goals",
            )

        waiting_approval = sum(1 for goal in goals if goal.status in [GoalStatus.submitted, GoalStatus.pending_approval])
        if waiting_approval > 0:
            return NextActionPayload(
                title="Manager review in progress",
                detail=f"{waiting_approval} submitted goals are waiting for manager approval.",
                action_url="/goals",
                action_label="View Goals",
            )

        # Goals approved: move to check-in flow
        now = datetime.now(timezone.utc)
        quarter = ((now.month - 1) // 3) + 1
        year = now.year

        checkins_result = await db.execute(
            select(Checkin).where(
                Checkin.employee_id == user.id,
                Checkin.cycle_id == cycle.id,
                Checkin.quarter == quarter,
                Checkin.year == year,
            )
        )
        quarter_checkins = list(checkins_result.scalars().all())
        used = len(quarter_checkins)
        cap = max(int(cycle.checkin_cap_per_quarter or 5), 1)

        if used < cap:
            return NextActionPayload(
                title=f"Your check-in is due in this cycle ({used}/{cap} used)",
                detail="Submit your next check-in to keep your manager updated.",
                action_url="/checkins",
                action_label="Submit Check-in",
                level="warning" if used == 0 else "info",
            )

        return NextActionPayload(
            title="Check-in cap reached",
            detail="You have completed all check-ins for the current quarter. Await cycle close and rating.",
            action_url="/reviews",
            action_label="View Reviews",
        )

    @staticmethod
    async def _manager_next_action(user: User, db: AsyncSession) -> NextActionPayload:
        cycle = await WorkflowService._active_cycle(user, db)
        if not cycle:
            return NextActionPayload(
                title="No active cycle",
                detail="Activate a cycle to receive team workflows.",
                action_url="/manager/dashboard",
                action_label="Refresh",
                level="warning",
            )

        pending_goals_result = await db.execute(
            select(Goal.id)
            .join(User, Goal.user_id == User.id)
            .where(
                User.manager_id == user.id,
                Goal.cycle_id == cycle.id,
                Goal.status.in_([GoalStatus.submitted, GoalStatus.pending_approval]),
            )
        )
        pending_goals = len(list(pending_goals_result.scalars().all()))
        if pending_goals > 0:
            return NextActionPayload(
                title=f"You have {pending_goals} goals to review",
                detail="Approve, request edits, or reject submitted goals.",
                action_url="/manager/approvals",
                action_label="Review Goals",
                level="warning",
            )

        pending_proposals_result = await db.execute(
            select(MeetingProposal.id).where(
                MeetingProposal.manager_id == user.id,
                MeetingProposal.status == MeetingProposalStatus.pending,
            )
        )
        pending_proposals = len(list(pending_proposals_result.scalars().all()))
        if pending_proposals > 0:
            return NextActionPayload(
                title=f"{pending_proposals} check-in meetings need scheduling approval",
                detail="Approve proposed meeting slots to keep check-in cadence healthy.",
                action_url="/manager/approvals",
                action_label="Review Meetings",
            )

        return NextActionPayload(
            title="Team is on track",
            detail="No urgent actions. Review stack ranking and coaching opportunities.",
            action_url="/manager/team-performance",
            action_label="Open Team Performance",
        )

    @staticmethod
    async def get_next_action(current_user: User, mode: UserRole, db: AsyncSession) -> dict:
        if mode == UserRole.employee:
            payload = await WorkflowService._employee_next_action(current_user, db)
        elif mode == UserRole.manager:
            payload = await WorkflowService._manager_next_action(current_user, db)
        elif mode == UserRole.hr:
            payload = NextActionPayload(
                title="Review calibration and reports",
                detail="Use analytics, calibration, and reports to drive decisions.",
                action_url="/hr/dashboard",
                action_label="Open HR Dashboard",
            )
        else:
            payload = NextActionPayload(
                title="Review organization signals",
                detail="Track org trends, 9-box outcomes, and succession priorities.",
                action_url="/leadership/dashboard",
                action_label="Open Leadership Dashboard",
            )

        return {
            "title": payload.title,
            "detail": payload.detail,
            "action_url": payload.action_url,
            "action_label": payload.action_label,
            "level": payload.level,
        }
