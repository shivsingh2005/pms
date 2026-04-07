from datetime import datetime, timedelta, timezone
import re
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.ai_service import AIService
from app.models.annual_operating_plan import AnnualOperatingPlan
from app.models.checkin import Checkin
from app.models.enums import CheckinStatus, GoalStatus, UserRole
from app.models.goal import Goal, GoalApprovalHistory, GoalChangeLog, GoalLineage
from app.models.goal_assignment import GoalAssignment
from app.models.kpi_library import KPILibrary
from app.models.performance_cycle import PerformanceCycle
from app.models.user import User
from app.services.cycle_guard import ensure_cycle_writable
from app.schemas.goal import GoalAssignRequest, GoalAssignmentOneRequest, GoalCascadeRequest, GoalCreate, GoalUpdate


class GoalService:
    MAX_WORKLOAD = 100.0

    @staticmethod
    def _role_key_from_text(value: str | None) -> str:
        text = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
        return text or "general"

    @staticmethod
    def _difficulty_from_weight(weight: float) -> str:
        if weight <= 30:
            return "easy"
        if weight <= 60:
            return "medium"
        return "hard"

    @staticmethod
    def _workload_status(workload_percent: float) -> str:
        if workload_percent < 50:
            return "low"
        if workload_percent < 80:
            return "medium"
        return "high"

    @staticmethod
    def _description_with_kpi(description: str | None, kpi: str | None) -> str | None:
        base = (description or "").strip()
        kpi_text = (kpi or "").strip()
        if not kpi_text:
            return base or None
        if not base:
            return f"KPI: {kpi_text}"
        return f"{base}\n\nKPI: {kpi_text}"

    @staticmethod
    def _goal_snapshot(goal: Goal) -> dict:
        return {
            "title": goal.title,
            "description": goal.description,
            "weightage": goal.weightage,
            "progress": goal.progress,
            "framework": goal.framework.value,
            "status": goal.status.value,
            "assigned_by": str(goal.assigned_by) if goal.assigned_by else None,
            "assigned_to": str(goal.assigned_to) if goal.assigned_to else None,
        }

    @staticmethod
    def _is_waiting_manager_review(goal: Goal) -> bool:
        return goal.status in {GoalStatus.pending_approval, GoalStatus.submitted}

    @staticmethod
    def _build_ai_assessment(goal: Goal) -> dict:
        text = f"{goal.title or ''} {goal.description or ''}".lower()
        measurable_tokens = ["%", "kpi", "reduce", "increase", "improve", "target", "deliver", "launch"]
        measurable_hits = sum(1 for token in measurable_tokens if token in text)

        clarity = min(1.0, round((len((goal.title or "").strip()) / 40.0), 2))
        measurability = min(1.0, round(measurable_hits / 4.0, 2))
        weight_fit = 1.0 if 5 <= float(goal.weightage) <= 60 else 0.7
        quality = round((0.4 * clarity) + (0.4 * measurability) + (0.2 * weight_fit), 2)

        recommendation = "approve"
        if quality < 0.55:
            recommendation = "request_edit"
        elif quality < 0.75:
            recommendation = "approve_with_note"

        return {
            "quality_score": quality,
            "clarity_score": clarity,
            "measurability_score": measurability,
            "weightage_fit": weight_fit,
            "recommendation": recommendation,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    async def _add_approval_event(
        goal: Goal,
        action: str,
        actor_id: UUID | None,
        from_status: GoalStatus | None,
        to_status: GoalStatus | None,
        db: AsyncSession,
        comment: str | None = None,
        ai_assessment: dict | None = None,
    ) -> None:
        event = GoalApprovalHistory(
            goal_id=goal.id,
            actor_id=actor_id,
            action=action,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value if to_status else None,
            comment=comment,
            ai_assessment=ai_assessment,
        )
        db.add(event)

    @staticmethod
    async def _log_goal_change(
        goal_id: UUID,
        changed_by: UUID | None,
        change_type: str,
        before_state: dict | None,
        after_state: dict | None,
        db: AsyncSession,
        note: str | None = None,
    ) -> None:
        log = GoalChangeLog(
            goal_id=goal_id,
            changed_by=changed_by,
            change_type=change_type,
            before_state=before_state,
            after_state=after_state,
            note=note,
        )
        db.add(log)

    @staticmethod
    async def _build_goal_grounding_context(manager: User, db: AsyncSession) -> str | None:
        current_year = datetime.now(timezone.utc).year
        aop_result = await db.execute(
            select(AnnualOperatingPlan)
            .where(
                AnnualOperatingPlan.organization_id == manager.organization_id,
                AnnualOperatingPlan.year == current_year,
            )
            .order_by(AnnualOperatingPlan.created_at.desc())
            .limit(5)
        )
        aop_rows = list(aop_result.scalars().all())

        team_result = await db.execute(
            select(User)
            .where(
                User.manager_id == manager.id,
                User.organization_id == manager.organization_id,
                User.is_active.is_(True),
            )
            .limit(30)
        )
        team_rows = list(team_result.scalars().all())
        titles = {row.title.strip() for row in team_rows if row.title and row.title.strip()}
        departments = {row.department.strip() for row in team_rows if row.department and row.department.strip()}

        kpi_snippets: list[str] = []
        if titles or departments:
            kpi_stmt = select(KPILibrary)
            if titles:
                kpi_stmt = kpi_stmt.where(KPILibrary.role.in_(list(titles)))
            if departments:
                kpi_stmt = kpi_stmt.where(KPILibrary.department.in_(list(departments)))

            kpi_result = await db.execute(
                kpi_stmt.order_by(KPILibrary.updated_at.desc()).limit(8)
            )
            for row in list(kpi_result.scalars().all()):
                kpi_snippets.append(f"{row.role}: {row.goal_title} (KPI: {row.suggested_kpi})")

        if not aop_rows and not kpi_snippets:
            return None

        aop_lines = [f"{row.year}-{row.department or 'org'}: {row.objective}" for row in aop_rows]
        fragments: list[str] = []
        if aop_lines:
            fragments.append("AOP context:\n" + "\n".join(f"- {line}" for line in aop_lines))
        if kpi_snippets:
            fragments.append("KPI library context:\n" + "\n".join(f"- {line}" for line in kpi_snippets))
        return "\n\n".join(fragments)

    @staticmethod
    def _external_role_intelligence(title: str | None, department: str | None) -> list[str]:
        text = f"{title or ''} {department or ''}".lower()
        if any(token in text for token in ["frontend", "ui", "react", "design"]):
            return [
                "Role benchmark: prioritize UI performance and accessibility outcomes.",
                "Role benchmark: include at least one cross-functional product collaboration goal.",
            ]
        if any(token in text for token in ["backend", "api", "platform", "database"]):
            return [
                "Role benchmark: include reliability, security, and latency goals.",
                "Role benchmark: maintain measurable service-level indicators.",
            ]
        if any(token in text for token in ["hr", "people", "talent"]):
            return [
                "Role benchmark: include employee experience and policy-adherence outcomes.",
                "Role benchmark: include measurable hiring, retention, or training outcomes.",
            ]
        return ["Role benchmark: include one execution goal, one collaboration goal, and one quality goal."]

    @staticmethod
    async def get_workload(user_id: UUID, db: AsyncSession) -> float:
        result = await db.execute(
            select(func.coalesce(func.sum(Goal.weightage), 0.0)).where(
                Goal.user_id == user_id,
                Goal.status != GoalStatus.rejected,
            )
        )
        return round(float(result.scalar() or 0.0), 1)

    @staticmethod
    async def _active_cycle_id_for_org(organization_id: UUID, db: AsyncSession) -> UUID | None:
        result = await db.execute(
            select(PerformanceCycle.id)
            .where(
                PerformanceCycle.organization_id == organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .order_by(PerformanceCycle.start_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_goal(current_user: User, payload: GoalCreate, db: AsyncSession) -> Goal:
        active_cycle_id = await GoalService._active_cycle_id_for_org(current_user.organization_id, db)
        source_type = "self_created" if current_user.role == UserRole.employee else "manager_assigned"
        goal = Goal(
            cycle_id=active_cycle_id,
            user_id=current_user.id,
            assigned_to=current_user.id,
            title=payload.title,
            description=payload.description,
            weightage=payload.weightage,
            status=GoalStatus.draft,
            progress=payload.progress,
            framework=payload.framework,
            source_type=source_type,
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        await GoalService._log_goal_change(goal.id, current_user.id, "created", None, GoalService._goal_snapshot(goal), db)
        await db.commit()
        return goal

    @staticmethod
    async def list_goals(current_user: User, mode: UserRole, db: AsyncSession) -> list[Goal]:
        stmt = select(Goal)
        if mode == UserRole.employee:
            stmt = stmt.where(Goal.user_id == current_user.id)
        elif mode == UserRole.manager:
            stmt = stmt.join(User, Goal.user_id == User.id).where(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )
        else:
            stmt = stmt.join(User, Goal.user_id == User.id).where(User.organization_id == current_user.organization_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_goal(goal_id: str, current_user: User, payload: GoalUpdate, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot update goal in a locked cycle")
        changes = payload.model_dump(exclude_unset=True)

        if current_user.role == UserRole.employee:
            if goal.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
            if not changes:
                return goal
            if set(changes.keys()) != {"progress"}:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can only update progress")

        if current_user.role == UserRole.manager:
            owner = await db.get(User, goal.user_id)
            if not owner or (owner.manager_id != current_user.id and owner.id != current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can edit only direct-report goals")

        before = GoalService._goal_snapshot(goal)
        for key, value in changes.items():
            setattr(goal, key, value)

        after = GoalService._goal_snapshot(goal)
        await GoalService._log_goal_change(goal.id, current_user.id, "updated", before, after, db)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def submit_goal(goal_id: str, current_user: User, db: AsyncSession) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot submit goal in a locked cycle")
        if goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can submit")
        if goal.status not in {GoalStatus.draft, GoalStatus.edit_requested}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft or edit-requested goals can be submitted")

        before = GoalService._goal_snapshot(goal)
        goal.status = GoalStatus.pending_approval
        goal.submitted_at = datetime.now(timezone.utc)
        goal.withdrawn_at = None
        goal.last_action_by = current_user.id
        goal.ai_assessment = GoalService._build_ai_assessment(goal)
        await GoalService._add_approval_event(
            goal=goal,
            action="submitted",
            actor_id=current_user.id,
            from_status=GoalStatus(before["status"]),
            to_status=goal.status,
            db=db,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(goal.id, current_user.id, "submitted_for_approval", before, GoalService._goal_snapshot(goal), db)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def approve_goal(goal_id: str, current_user: User, db: AsyncSession, manager_comment: str | None = None) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot approve goal in a locked cycle")

        owner = await db.get(User, goal.user_id)
        if not owner or not owner.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal owner not found")

        if current_user.role == UserRole.manager:
            if owner.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can approve only direct-report goals")
            if owner.id == current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot approve their own goals")
        elif current_user.organization_id != owner.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization approval is not allowed")
        if not GoalService._is_waiting_manager_review(goal):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goal is not awaiting manager review")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        goal.status = GoalStatus.approved
        goal.approved_at = datetime.now(timezone.utc)
        goal.rejected_at = None
        goal.edit_requested_at = None
        goal.manager_comment = manager_comment
        goal.last_action_by = current_user.id
        await GoalService._add_approval_event(
            goal=goal,
            action="approved",
            actor_id=current_user.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=manager_comment,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(goal.id, current_user.id, "approved", before, GoalService._goal_snapshot(goal), db, note=manager_comment)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def reject_goal(goal_id: str, current_user: User, db: AsyncSession, manager_comment: str | None = None) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot reject goal in a locked cycle")

        owner = await db.get(User, goal.user_id)
        if not owner or not owner.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal owner not found")

        if current_user.role == UserRole.manager:
            if owner.manager_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can reject only direct-report goals")
            if owner.id == current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot reject their own goals")
        elif current_user.organization_id != owner.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization rejection is not allowed")
        if not GoalService._is_waiting_manager_review(goal):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goal is not awaiting manager review")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        goal.status = GoalStatus.rejected
        goal.rejected_at = datetime.now(timezone.utc)
        goal.edit_requested_at = None
        goal.manager_comment = manager_comment
        goal.last_action_by = current_user.id
        await GoalService._add_approval_event(
            goal=goal,
            action="rejected",
            actor_id=current_user.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=manager_comment,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(goal.id, current_user.id, "rejected", before, GoalService._goal_snapshot(goal), db, note=manager_comment)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def self_create_goal(employee: User, payload: GoalCreate, db: AsyncSession) -> Goal:
        if employee.role != UserRole.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can self-create goals")

        active_cycle_id = await GoalService._active_cycle_id_for_org(employee.organization_id, db)
        await ensure_cycle_writable(db, active_cycle_id, locked_detail="Cannot create goals in a locked cycle")

        current_weight = await GoalService.get_workload(employee.id, db)
        projected = round(current_weight + float(payload.weightage), 1)
        if projected > 100:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Total goal weightage cannot exceed 100% (projected: {projected}%)")

        goal = Goal(
            cycle_id=active_cycle_id,
            user_id=employee.id,
            assigned_to=employee.id,
            assigned_by=employee.manager_id,
            title=payload.title,
            description=payload.description,
            weightage=payload.weightage,
            status=GoalStatus.draft,
            progress=0,
            framework=payload.framework,
            source_type="self_created",
            last_action_by=employee.id,
        )
        db.add(goal)
        await db.flush()

        await GoalService._add_approval_event(
            goal=goal,
            action="created",
            actor_id=employee.id,
            from_status=None,
            to_status=goal.status,
            db=db,
        )
        await GoalService._log_goal_change(goal.id, employee.id, "self_created", None, GoalService._goal_snapshot(goal), db)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def submit_self_goal_for_approval(
        goal_id: str,
        employee: User,
        db: AsyncSession,
        notes: str | None = None,
    ) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if goal.user_id != employee.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can submit goal")
        if goal.source_type != "self_created":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only self-created goals can use this workflow")
        if goal.status not in {GoalStatus.draft, GoalStatus.edit_requested}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goal is not in a submittable state")
        if not employee.manager_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No manager assigned for approval")

        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot submit goal in a locked cycle")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        goal.status = GoalStatus.pending_approval
        goal.submitted_at = datetime.now(timezone.utc)
        goal.withdrawn_at = None
        goal.submission_notes = notes
        goal.last_action_by = employee.id
        goal.ai_assessment = GoalService._build_ai_assessment(goal)

        await GoalService._add_approval_event(
            goal=goal,
            action="submitted",
            actor_id=employee.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=notes,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(
            goal.id,
            employee.id,
            "submitted_for_approval",
            before,
            GoalService._goal_snapshot(goal),
            db,
            note=notes,
        )
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def withdraw_goal_request(
        goal_id: str,
        employee: User,
        db: AsyncSession,
        reason: str | None = None,
    ) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if goal.user_id != employee.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can withdraw goal")
        if not GoalService._is_waiting_manager_review(goal):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending goals can be withdrawn")

        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot withdraw goal in a locked cycle")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        goal.status = GoalStatus.withdrawn
        goal.withdrawn_at = datetime.now(timezone.utc)
        goal.last_action_by = employee.id

        await GoalService._add_approval_event(
            goal=goal,
            action="withdrawn",
            actor_id=employee.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=reason,
        )
        await GoalService._log_goal_change(goal.id, employee.id, "withdrawn", before, GoalService._goal_snapshot(goal), db, note=reason)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def list_manager_pending_goals(manager: User, db: AsyncSession) -> list[tuple[Goal, User]]:
        result = await db.execute(
            select(Goal, User)
            .join(User, Goal.user_id == User.id)
            .where(
                User.manager_id == manager.id,
                User.organization_id == manager.organization_id,
                Goal.source_type == "self_created",
                Goal.status.in_([GoalStatus.pending_approval, GoalStatus.submitted]),
            )
            .order_by(Goal.submitted_at.desc().nullslast(), Goal.created_at.desc())
        )
        return list(result.all())

    @staticmethod
    async def request_goal_edit(
        goal_id: str,
        manager: User,
        db: AsyncSession,
        comment: str | None = None,
    ) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or owner.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can review only direct-report goals")
        if not GoalService._is_waiting_manager_review(goal):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goal is not awaiting manager review")

        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot request edits in a locked cycle")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        goal.status = GoalStatus.edit_requested
        goal.edit_requested_at = datetime.now(timezone.utc)
        goal.manager_comment = comment
        goal.last_action_by = manager.id

        await GoalService._add_approval_event(
            goal=goal,
            action="edit_requested",
            actor_id=manager.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=comment,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(goal.id, manager.id, "edit_requested", before, GoalService._goal_snapshot(goal), db, note=comment)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def manager_edit_and_approve_goal(
        goal_id: str,
        manager: User,
        payload: GoalUpdate,
        db: AsyncSession,
        comment: str | None = None,
    ) -> Goal:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or owner.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can review only direct-report goals")
        if not GoalService._is_waiting_manager_review(goal):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Goal is not awaiting manager review")

        await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot edit or approve goal in a locked cycle")

        before = GoalService._goal_snapshot(goal)
        previous_status = goal.status
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(goal, key, value)
        goal.status = GoalStatus.approved
        goal.approved_at = datetime.now(timezone.utc)
        goal.manager_comment = comment
        goal.last_action_by = manager.id

        await GoalService._add_approval_event(
            goal=goal,
            action="manager_edit_approved",
            actor_id=manager.id,
            from_status=previous_status,
            to_status=goal.status,
            db=db,
            comment=comment,
            ai_assessment=goal.ai_assessment,
        )
        await GoalService._log_goal_change(goal.id, manager.id, "manager_edit_approved", before, GoalService._goal_snapshot(goal), db, note=comment)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def get_goal_approval_history(goal_id: str, current_user: User, db: AsyncSession) -> list[GoalApprovalHistory]:
        goal = await db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or owner.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if current_user.role == UserRole.employee and goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can view only own goal history")
        if current_user.role == UserRole.manager and owner.manager_id != current_user.id and owner.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can view only own or direct-report goal history")

        result = await db.execute(
            select(GoalApprovalHistory)
            .where(GoalApprovalHistory.goal_id == goal.id)
            .order_by(GoalApprovalHistory.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_self_goal_summary(employee: User, db: AsyncSession) -> dict:
        result = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == employee.id,
                Goal.source_type == "self_created",
                Goal.status != GoalStatus.rejected,
            )
        )
        goals = list(result.scalars().all())
        return {
            "total_weightage": round(sum(float(goal.weightage or 0) for goal in goals), 1),
            "pending_approval_count": sum(1 for goal in goals if GoalService._is_waiting_manager_review(goal)),
            "edit_requested_count": sum(1 for goal in goals if goal.status == GoalStatus.edit_requested),
            "approved_count": sum(1 for goal in goals if goal.status == GoalStatus.approved),
        }

    @staticmethod
    async def assign_goals(manager: User, payload: GoalAssignRequest, db: AsyncSession) -> list[Goal]:
        target_user = await db.get(User, payload.employee_id)
        if not target_user or not target_user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if manager.role == UserRole.manager and target_user.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only assign goals to direct reports")

        if target_user.organization_id != manager.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization assignment is not allowed")

        desired_status = GoalStatus.rejected if payload.reject else GoalStatus.approved if payload.approve else GoalStatus.draft
        active_cycle_id = await GoalService._active_cycle_id_for_org(manager.organization_id, db)
        saved_goals: list[Goal] = []

        for item in payload.goals:
            if item.goal_id:
                goal = await db.get(Goal, item.goal_id)
                if not goal or goal.user_id != payload.employee_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found for employee")
                await ensure_cycle_writable(db, goal.cycle_id, locked_detail="Cannot reassign goal in a locked cycle")
            else:
                goal = Goal(
                    cycle_id=active_cycle_id,
                    user_id=payload.employee_id,
                    assigned_to=payload.employee_id,
                    assigned_by=manager.id,
                    title=item.title,
                    description=GoalService._description_with_kpi(item.description, item.kpi),
                    weightage=item.weightage,
                    progress=item.progress,
                    framework=item.framework,
                    status=desired_status,
                    is_ai_generated=payload.is_ai_generated,
                )
                db.add(goal)
                await db.flush()
                await GoalService._log_goal_change(goal.id, manager.id, "assigned", None, GoalService._goal_snapshot(goal), db)
                saved_goals.append(goal)
                continue

            before = GoalService._goal_snapshot(goal)
            goal.title = item.title
            goal.description = GoalService._description_with_kpi(item.description, item.kpi)
            goal.weightage = item.weightage
            goal.framework = item.framework
            goal.progress = item.progress
            goal.status = desired_status
            goal.assigned_by = manager.id
            goal.assigned_to = payload.employee_id
            goal.is_ai_generated = payload.is_ai_generated
            if goal.cycle_id is None:
                goal.cycle_id = active_cycle_id
            await GoalService._log_goal_change(goal.id, manager.id, "reassigned", before, GoalService._goal_snapshot(goal), db)
            saved_goals.append(goal)

        await db.commit()

        for goal in saved_goals:
            await db.refresh(goal)

        return saved_goals

    @staticmethod
    async def get_role_goal_recommendations(
        manager: User,
        organization_objectives: str | None,
        db: AsyncSession,
    ) -> dict:
        if manager.role != UserRole.manager:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can generate role goal recommendations")

        ai = AIService()
        grounding_context = await GoalService._build_goal_grounding_context(manager, db)
        role_intelligence = GoalService._external_role_intelligence("manager", manager.department)
        try:
            generated = await ai.generate_team_goals(
                requester=manager,
                manager_id=str(manager.id),
                organization_objectives=organization_objectives,
                grounding_context=grounding_context,
                role_intelligence=role_intelligence,
                db=db,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except RuntimeError as exc:
            message = str(exc)
            if "Quarterly AI usage cap reached" in message:
                generated = await GoalService._fallback_role_goal_recommendations(manager, db)
            else:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message) from exc

        clusters: dict[str, list[dict]] = {}
        role_labels: dict[str, str] = {}
        seen_titles: dict[str, set[str]] = {}

        for employee in generated.get("employees", []):
            role_text = str(employee.get("role", "")).strip() or "General"
            role_key = GoalService._role_key_from_text(role_text)
            if role_key not in role_labels:
                role_labels[role_key] = role_text
            if role_key not in clusters:
                clusters[role_key] = []
            if role_key not in seen_titles:
                seen_titles[role_key] = set()

            for goal in employee.get("goals", []):
                title = str(goal.get("title", "")).strip()
                description = str(goal.get("description", "")).strip()
                weight = float(goal.get("weightage", 0) or 0)
                if not title or not description or weight <= 0:
                    continue

                title_key = title.lower()
                if title_key in seen_titles[role_key]:
                    continue
                seen_titles[role_key].add(title_key)

                clusters[role_key].append(
                    {
                        "title": title,
                        "description": description,
                        "difficulty": GoalService._difficulty_from_weight(weight),
                        "suggested_weight": min(100.0, max(0.0, round(weight, 1))),
                        "kpi": str(goal.get("kpi", "")).strip() or None,
                    }
                )

        cluster_payload = [
            {
                "role": role_labels.get(role_key, role_key.replace("-", " ").title()),
                "goals": goals,
            }
            for role_key, goals in sorted(clusters.items(), key=lambda item: item[0])
        ]

        return {
            "manager_id": manager.id,
            "clusters": cluster_payload,
        }

    @staticmethod
    async def _fallback_role_goal_recommendations(manager: User, db: AsyncSession) -> dict:
        team_result = await db.execute(
            select(User.id, User.name, User.title, User.role, User.department)
            .where(
                User.manager_id == manager.id,
                User.organization_id == manager.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
            .order_by(User.name.asc())
        )
        team_rows = team_result.all()

        role_templates: dict[str, list[dict]] = {
            "frontend": [
                {
                    "title": "Improve UI responsiveness",
                    "description": "Reduce interaction latency and optimize critical rendering paths.",
                    "kpi": "Improve Core Web Vitals for primary flows",
                    "weightage": 35,
                },
                {
                    "title": "Increase component reuse",
                    "description": "Consolidate duplicated UI patterns into shared components.",
                    "kpi": "Reduce duplicate component variants by 30%",
                    "weightage": 30,
                },
                {
                    "title": "Strengthen frontend quality",
                    "description": "Raise confidence with targeted unit and integration coverage.",
                    "kpi": "Raise UI regression test pass stability to 95%",
                    "weightage": 35,
                },
            ],
            "backend": [
                {
                    "title": "Improve API reliability",
                    "description": "Reduce avoidable service errors and improve endpoint resilience.",
                    "kpi": "Cut avoidable 5xx incidents by 25%",
                    "weightage": 35,
                },
                {
                    "title": "Optimize query performance",
                    "description": "Tune slow paths and improve backend response consistency.",
                    "kpi": "Reduce p95 latency for core APIs",
                    "weightage": 30,
                },
                {
                    "title": "Harden data integrity",
                    "description": "Improve validation and consistency checks for critical writes.",
                    "kpi": "Zero critical integrity regressions in sprint",
                    "weightage": 35,
                },
            ],
            "others": [
                {
                    "title": "Improve execution quality",
                    "description": "Deliver commitments with clear ownership and timely updates.",
                    "kpi": "Complete 90% of planned work each cycle",
                    "weightage": 35,
                },
                {
                    "title": "Strengthen cross-team collaboration",
                    "description": "Resolve handoff bottlenecks with adjacent functions.",
                    "kpi": "Resolve one cross-team dependency each cycle",
                    "weightage": 30,
                },
                {
                    "title": "Improve stakeholder communication",
                    "description": "Make status, risks, and decisions transparent to stakeholders.",
                    "kpi": "Maintain weekly updates with clear risk register",
                    "weightage": 35,
                },
            ],
        }

        employees: list[dict] = []
        for user_id, name, title, role, department in team_rows:
            role_key = GoalService._role_key_from_text(str(title or getattr(role, "value", role)))
            employees.append(
                {
                    "employee_id": str(user_id),
                    "employee_name": name,
                    "role": str(title or getattr(role, "value", role)),
                    "department": department or "General",
                    "goals": role_templates.get(role_key, role_templates["others"]),
                }
            )

        return {
            "manager_id": str(manager.id),
            "employees": employees,
        }

    @staticmethod
    async def list_assignment_candidates(manager: User, role_key: str, db: AsyncSession) -> list[dict]:
        normalized_role = GoalService._role_key_from_text(role_key)

        team_result = await db.execute(
            select(User)
            .where(
                User.manager_id == manager.id,
                User.organization_id == manager.organization_id,
                User.is_active.is_(True),
                User.role == UserRole.employee,
            )
            .order_by(User.name.asc())
        )
        team_members = list(team_result.scalars().all())

        rows: list[dict] = []
        for member in team_members:
            member_role_key = GoalService._role_key_from_text(member.title or member.role.value)
            if member_role_key != normalized_role:
                continue

            goals_result = await db.execute(
                select(func.count(Goal.id), func.coalesce(func.sum(Goal.weightage), 0.0)).where(
                    Goal.user_id == member.id,
                    Goal.status != GoalStatus.rejected,
                )
            )
            goal_count, total_weight = goals_result.one()

            checkins_result = await db.execute(
                select(func.count(Checkin.id)).where(
                    Checkin.employee_id == member.id,
                    Checkin.status.in_([CheckinStatus.draft, CheckinStatus.submitted]),
                )
            )
            active_checkins = int(checkins_result.scalar() or 0)

            workload_percent = round(float(total_weight or 0.0), 1)
            rows.append(
                {
                    "employee_id": member.id,
                    "employee_name": member.name,
                    "role": member.title or member.role.value,
                    "role_key": member_role_key,
                    "goal_count": int(goal_count or 0),
                    "total_weightage": workload_percent,
                    "active_checkins": active_checkins,
                    "workload_percent": workload_percent,
                    "workload_status": GoalService._workload_status(workload_percent),
                }
            )

        return rows

    @staticmethod
    async def assign_single_goal(
        manager: User,
        payload: GoalAssignmentOneRequest,
        db: AsyncSession,
    ) -> tuple[Goal, float, str, str | None]:
        employee = await db.get(User, payload.employee_id)
        if not employee or not employee.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        if employee.organization_id != manager.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization assignment is not allowed")

        if manager.role == UserRole.manager and employee.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can assign goals only to direct reports")

        requested_role_key = GoalService._role_key_from_text(payload.role)
        employee_role_key = GoalService._role_key_from_text(employee.title or employee.role.value)
        if requested_role_key != employee_role_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal role does not match employee role")

        current_workload = await GoalService.get_workload(employee.id, db)
        projected_workload = round(current_workload + float(payload.weightage), 1)
        if projected_workload > GoalService.MAX_WORKLOAD and not payload.allow_overload:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Assignment exceeds workload limit: {projected_workload}%",
            )

        active_cycle_id = await GoalService._active_cycle_id_for_org(manager.organization_id, db)
        await ensure_cycle_writable(db, active_cycle_id, locked_detail="Cannot assign goals in a locked cycle")

        goal = Goal(
            cycle_id=active_cycle_id,
            user_id=employee.id,
            assigned_to=employee.id,
            assigned_by=manager.id,
            title=payload.title,
            description=GoalService._description_with_kpi(payload.description, payload.kpi),
            weightage=payload.weightage,
            progress=payload.progress,
            framework=payload.framework,
            status=GoalStatus.approved if payload.approve else GoalStatus.draft,
            is_ai_generated=payload.is_ai_generated,
        )
        db.add(goal)
        await db.flush()

        assignment = GoalAssignment(
            goal_id=goal.id,
            employee_id=employee.id,
            manager_id=manager.id,
            role_key=requested_role_key,
            weight=payload.weightage,
            status="approved" if payload.approve else "assigned",
        )
        db.add(assignment)
        await GoalService._log_goal_change(goal.id, manager.id, "assigned", None, GoalService._goal_snapshot(goal), db)

        await db.commit()
        await db.refresh(goal)

        warning = None
        if projected_workload > 100:
            warning = "Workload exceeds 100%"
        elif projected_workload >= 80:
            warning = "Workload is high"

        return goal, projected_workload, GoalService._workload_status(projected_workload), warning

    @staticmethod
    async def cascade_goal(
        manager: User,
        payload: GoalCascadeRequest,
        db: AsyncSession,
    ) -> tuple[UUID, list[UUID]]:
        parent_goal = await db.get(Goal, payload.parent_goal_id)
        if not parent_goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent goal not found")

        parent_owner = await db.get(User, parent_goal.user_id)
        if not parent_owner or parent_owner.organization_id != manager.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization lineage is not allowed")

        if manager.role == UserRole.manager and parent_owner.id != manager.id and parent_owner.manager_id != manager.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can cascade only own or direct-report goals")

        if not payload.children:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one child goal is required")

        total_weight = sum(max(float(row.weightage), 0.0) for row in payload.children)
        if total_weight <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Child goal weights must be greater than zero")

        child_ids: list[UUID] = []
        for child in payload.children:
            employee = await db.get(User, child.employee_id)
            if not employee or not employee.is_active:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cascade target employee not found")
            if employee.organization_id != manager.organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization cascade target is not allowed")
            if manager.role == UserRole.manager and employee.manager_id != manager.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can cascade goals only to direct reports")

            contribution = float(child.weightage)
            if payload.normalize_weights:
                contribution = round((contribution / total_weight) * 100.0, 2)

            goal = Goal(
                cycle_id=parent_goal.cycle_id,
                user_id=employee.id,
                assigned_to=employee.id,
                assigned_by=manager.id,
                title=child.title,
                description=GoalService._description_with_kpi(child.description, child.kpi),
                weightage=child.weightage,
                progress=child.progress,
                framework=child.framework,
                status=GoalStatus.approved,
                is_ai_generated=True,
            )
            db.add(goal)
            await db.flush()

            edge = GoalLineage(
                parent_goal_id=parent_goal.id,
                child_goal_id=goal.id,
                contribution_percentage=contribution,
                created_by=manager.id,
            )
            db.add(edge)
            await GoalService._log_goal_change(goal.id, manager.id, "cascade_child_created", None, GoalService._goal_snapshot(goal), db, note="Created via cascading")
            child_ids.append(goal.id)

        await db.commit()
        return parent_goal.id, child_ids

    @staticmethod
    async def get_goal_lineage(goal_id: UUID | str, current_user: User, db: AsyncSession) -> dict:
        try:
            goal_uuid = UUID(str(goal_id))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid goal id") from exc
        root_goal = await db.get(Goal, goal_uuid)
        if not root_goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, root_goal.user_id)
        if not owner or owner.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if current_user.role == UserRole.employee and root_goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can view only own lineage")

        node_ids: set[UUID] = {root_goal.id}
        edges_result = await db.execute(
            select(GoalLineage).where(
                (GoalLineage.parent_goal_id == root_goal.id) | (GoalLineage.child_goal_id == root_goal.id)
            )
        )
        edges = list(edges_result.scalars().all())
        for edge in edges:
            node_ids.add(edge.parent_goal_id)
            node_ids.add(edge.child_goal_id)

        goals_result = await db.execute(select(Goal).where(Goal.id.in_(list(node_ids))))
        goals = list(goals_result.scalars().all())
        goal_map = {goal.id: goal for goal in goals}

        return {
            "root_goal_id": root_goal.id,
            "nodes": [
                {
                    "goal_id": goal.id,
                    "user_id": goal.user_id,
                    "title": goal.title,
                    "framework": goal.framework,
                    "weightage": goal.weightage,
                    "progress": goal.progress,
                    "status": goal.status,
                }
                for goal in goals
                if goal.id in goal_map
            ],
            "edges": [
                {
                    "parent_goal_id": edge.parent_goal_id,
                    "child_goal_id": edge.child_goal_id,
                    "contribution_percentage": edge.contribution_percentage,
                }
                for edge in edges
            ],
        }

    @staticmethod
    async def get_goal_changes(goal_id: UUID | str, current_user: User, db: AsyncSession) -> list[GoalChangeLog]:
        try:
            goal_uuid = UUID(str(goal_id))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid goal id") from exc
        goal = await db.get(Goal, goal_uuid)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        owner = await db.get(User, goal.user_id)
        if not owner or owner.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if current_user.role == UserRole.employee and goal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can view only own goal logs")

        result = await db.execute(
            select(GoalChangeLog)
            .where(GoalChangeLog.goal_id == goal.id)
            .order_by(GoalChangeLog.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_goal_drift(current_user: User, mode: UserRole, db: AsyncSession) -> list[dict]:
        horizon = datetime.now(timezone.utc) - timedelta(days=14)
        stmt = select(Goal).where(
            Goal.status.in_([GoalStatus.submitted, GoalStatus.pending_approval, GoalStatus.approved]),
            Goal.created_at <= horizon,
        )

        if mode == UserRole.employee:
            stmt = stmt.where(Goal.user_id == current_user.id)
        elif mode == UserRole.manager:
            stmt = stmt.join(User, Goal.user_id == User.id).where(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )
        else:
            stmt = stmt.join(User, Goal.user_id == User.id).where(User.organization_id == current_user.organization_id)

        result = await db.execute(stmt.order_by(Goal.weightage.desc()))
        goals = list(result.scalars().all())

        drifts: list[dict] = []
        for goal in goals:
            if goal.progress >= 70:
                continue

            score = round(max(goal.weightage - goal.progress, 0.0), 1)
            if score < 20:
                continue

            reason = "High-weight goal with low progress"
            if goal.progress < 20:
                reason = "Progress stagnation risk"

            drifts.append(
                {
                    "goal_id": goal.id,
                    "user_id": goal.user_id,
                    "title": goal.title,
                    "weightage": goal.weightage,
                    "progress": goal.progress,
                    "drift_score": score,
                    "reason": reason,
                }
            )

        return drifts
