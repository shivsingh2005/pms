from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict
from sqlalchemy import func, select
from app.ai.gemini_client import GeminiClient, GeminiClientError
from app.ai import prompts
from app.models.goal import Goal
from app.models.ai_usage_log import AIUsageLog
from app.models.enums import GoalStatus, UserRole
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


class AIService:
    FEATURE_ACCESS: dict[str, set[UserRole]] = {
        "chat_assistant": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership, UserRole.admin},
        "goal_suggestions": {UserRole.employee, UserRole.admin},
        "career_growth": {UserRole.employee, UserRole.admin},
        "checkin_summary": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.admin},
        "performance_review": {UserRole.manager, UserRole.admin},
        "feedback_coaching": {UserRole.manager, UserRole.admin},
        "training_suggestions": {UserRole.hr, UserRole.admin},
        "decision_intelligence": {UserRole.manager, UserRole.hr, UserRole.leadership, UserRole.admin},
        "role_based_goal_generation": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership, UserRole.admin},
        "team_goal_allotment": {UserRole.manager, UserRole.hr, UserRole.admin},
    }

    ROLE_FOCUS_AREAS: dict[str, list[str]] = {
        "backend": ["API performance", "Database optimization", "Service security", "Automated testing", "Developer experience"],
        "frontend": ["Core web vitals", "UX accessibility", "Design system quality", "Automated UI testing", "Frontend observability"],
        "devops": ["Deployment reliability", "Cost optimization", "Monitoring quality", "Infrastructure security", "Release automation"],
        "qa": ["Regression coverage", "Test automation", "Defect prevention", "Performance testing", "Release quality gates"],
        "data": ["Data quality", "Pipeline reliability", "Model performance", "Experiment cadence", "Stakeholder reporting"],
        "product": ["Roadmap execution", "Discovery quality", "Cross-team alignment", "Outcome measurement", "Customer feedback loops"],
    }

    def __init__(self, client: GeminiClient | None = None) -> None:
        if client is not None:
            self.client = client
            return

        try:
            self.client = GeminiClient()
        except Exception:
            self.client = None

    @staticmethod
    def _quarter_now() -> tuple[int, int]:
        now = datetime.now(timezone.utc)
        quarter = ((now.month - 1) // 3) + 1
        return quarter, now.year

    async def _check_rbac(self, feature_name: str, user: User) -> None:
        allowed = self.FEATURE_ACCESS.get(feature_name, set())
        if user.role not in allowed:
            raise PermissionError("Role is not allowed for this AI feature")

    async def _enforce_quarter_limit(self, user: User, db: AsyncSession) -> None:
        return

    async def _log_usage(
        self,
        user_id: UUID,
        feature_name: str,
        prompt_tokens: int,
        response_tokens: int,
        db: AsyncSession,
    ) -> None:
        usage = AIUsageLog(
            user_id=user_id,
            feature_name=feature_name,
            prompt_tokens=max(prompt_tokens, 0),
            response_tokens=max(response_tokens, 0),
        )
        db.add(usage)
        await db.commit()

    async def _execute(
        self,
        user: User,
        feature_name: str,
        prompt: str,
        fallback: dict,
        db: AsyncSession,
    ) -> dict:
        await self._check_rbac(feature_name, user)
        try:
            await self._enforce_quarter_limit(user, db)
        except RuntimeError:
            pass

        if self.client is None:
            await self._log_usage(user.id, feature_name, 0, 0, db)
            return fallback

        try:
            payload, result = await self.client.generate_json(prompt)
            await self._log_usage(user.id, feature_name, result.prompt_tokens, result.response_tokens, db)
            return payload
        except GeminiClientError:
            await self._log_usage(user.id, feature_name, 0, 0, db)
            return fallback
        except Exception:
            await self._log_usage(user.id, feature_name, 0, 0, db)
            return fallback

    @classmethod
    def _resolve_focus_catalog(cls, title: str | None) -> list[str]:
        if not title:
            return ["Execution quality", "Cross-team collaboration", "Delivery predictability", "Technical excellence", "Customer impact"]

        lower_title = title.lower()
        for key, areas in cls.ROLE_FOCUS_AREAS.items():
            if key in lower_title:
                return areas

        return ["Execution quality", "Cross-team collaboration", "Delivery predictability", "Process improvement", "Stakeholder communication"]

    @classmethod
    def _pick_focus_area(cls, title: str | None, member_index: int) -> str:
        catalog = cls._resolve_focus_catalog(title)
        return catalog[(member_index - 1) % len(catalog)]

    async def generate_role_based_goals(
        self,
        requester: User,
        target_user_id: str,
        organization_objectives: str | None,
        db: AsyncSession,
    ) -> dict:
        await self._check_rbac("role_based_goal_generation", requester)

        try:
            target_uuid = UUID(target_user_id)
        except ValueError as exc:
            raise PermissionError("Invalid target user id") from exc

        target_user = await db.get(User, target_uuid)
        if not target_user or not target_user.is_active:
            raise PermissionError("Target user not found")

        if requester.role == UserRole.employee and requester.id != target_user.id:
            raise PermissionError("Employees can generate goals only for themselves")

        if requester.role == UserRole.manager and target_user.manager_id != requester.id and target_user.id != requester.id:
            raise PermissionError("Managers can generate goals only for direct reports")

        if requester.role != UserRole.admin and target_user.organization_id != requester.organization_id:
            raise PermissionError("Cross-organization access is not allowed")

        title = (target_user.title or "Individual Contributor").strip()
        department = (target_user.department or "General").strip()

        peers_result = await db.execute(
            select(User)
            .where(
                User.organization_id == target_user.organization_id,
                User.title == target_user.title,
                User.is_active.is_(True),
            )
            .order_by(User.name.asc(), User.id.asc())
        )
        peers = list(peers_result.scalars().all())

        if not peers:
            peers = [target_user]

        member_index = next((idx for idx, member in enumerate(peers, start=1) if member.id == target_user.id), 1)
        team_size = len(peers)
        focus_area = self._pick_focus_area(title, member_index)

        prompt = prompts.role_based_goal_generation_prompt(
            role_title=title,
            role=target_user.role.value,
            department=department,
            team_size=team_size,
            member_index=member_index,
            focus_area=focus_area,
            objective=organization_objectives,
        )

        fallback = {
            "goals": [
                {
                    "title": f"Improve {focus_area}",
                    "description": f"Deliver measurable improvements in {focus_area.lower()} for the {department} team.",
                    "kpi": "Deliver at least 2 measurable improvements by quarter end",
                    "weightage": 30,
                },
                {
                    "title": "Strengthen execution reliability",
                    "description": "Improve predictability and quality of sprint deliverables.",
                    "kpi": "Maintain at least 90% planned-to-completed sprint commitment",
                    "weightage": 25,
                },
                {
                    "title": "Increase collaboration impact",
                    "description": "Partner with adjacent functions to remove delivery bottlenecks.",
                    "kpi": "Close 3 cross-team dependencies with documented outcomes",
                    "weightage": 20,
                },
                {
                    "title": "Operational excellence",
                    "description": "Reduce cycle friction through process and tooling improvements.",
                    "kpi": "Reduce average cycle time by 15%",
                    "weightage": 25,
                },
            ]
        }
        payload = await self._execute(requester, "role_based_goal_generation", prompt, fallback, db)

        return {
            "user_id": str(target_user.id),
            "title": title,
            "department": department,
            "team_size": team_size,
            "focus_area": focus_area,
            "goals": payload.get("goals", fallback["goals"]),
        }

    async def generate_goal_suggestions(self, user: User, role: str, department: str, organization_objectives: str, db: AsyncSession) -> dict:
        prompt = prompts.goal_suggestion_prompt(role=role, department=department, objective=organization_objectives)
        fallback = {
            "goals": [
                {
                    "title": "Improve execution quality",
                    "description": "Deliver key deliverables with fewer defects",
                    "kpi": "Reduce rework by 20%",
                    "weightage": 25,
                },
                {
                    "title": "Increase cross-team collaboration",
                    "description": "Partner with adjacent teams on shared outcomes",
                    "kpi": "Complete 2 cross-team initiatives",
                    "weightage": 25,
                },
                {
                    "title": "Improve delivery predictability",
                    "description": "Meet planned sprint commitments consistently",
                    "kpi": "Maintain 90% sprint predictability",
                    "weightage": 25,
                },
                {
                    "title": "Build domain expertise",
                    "description": "Develop deeper knowledge in core functional area",
                    "kpi": "Complete one domain certification",
                    "weightage": 25,
                },
            ]
        }
        return await self._execute(user, "goal_suggestions", prompt, fallback, db)

    async def generate_team_goals(
        self,
        requester: User,
        manager_id: str,
        organization_objectives: str | None,
        db: AsyncSession,
    ) -> dict:
        await self._check_rbac("team_goal_allotment", requester)

        try:
            manager_uuid = UUID(manager_id)
        except ValueError as exc:
            raise PermissionError("Invalid manager id") from exc

        manager = await db.get(User, manager_uuid)
        if not manager or not manager.is_active:
            raise PermissionError("Manager not found")

        if requester.role == UserRole.manager and requester.id != manager.id:
            raise PermissionError("Managers can generate goals only for themselves")

        if requester.role != UserRole.admin and requester.organization_id != manager.organization_id:
            raise PermissionError("Cross-organization access is not allowed")

        team_result = await db.execute(
            select(User)
            .where(
                User.manager_id == manager.id,
                User.organization_id == manager.organization_id,
                User.is_active.is_(True),
            )
            .order_by(User.name.asc())
        )
        members = list(team_result.scalars().all())
        if not members:
            return {"manager_id": str(manager.id), "team_structure": [], "employees": []}

        role_buckets: dict[str, list[User]] = defaultdict(list)
        for member in members:
            role_key = (member.title or member.role.value).strip()
            role_buckets[role_key].append(member)

        team_structure = [f"{role}: {len(items)}" for role, items in sorted(role_buckets.items(), key=lambda item: item[0])]

        workloads_result = await db.execute(
            select(Goal.user_id, func.coalesce(func.sum(Goal.weightage), 0.0), func.count(Goal.id))
            .where(Goal.user_id.in_([member.id for member in members]), Goal.status != GoalStatus.rejected)
            .group_by(Goal.user_id)
        )
        workload_map: dict[str, float] = {}
        goal_count_map: dict[str, int] = {}
        for user_id, workload, count in workloads_result.all():
            workload_map[str(user_id)] = float(workload or 0.0)
            goal_count_map[str(user_id)] = int(count or 0)

        employee_lines: list[str] = []
        fallback_employees: list[dict] = []
        for role_name, group in role_buckets.items():
            ordered = sorted(group, key=lambda item: item.name.lower())
            for idx, member in enumerate(ordered, start=1):
                focus_area = self._pick_focus_area(role_name, idx)
                employee_lines.append(
                    f"{member.id} | {member.name} | {role_name} | dept={member.department or 'General'} | workload={round(workload_map.get(str(member.id), 0.0), 1)} | focus={focus_area}"
                )

                fallback_employees.append(
                    {
                        "employee_id": str(member.id),
                        "employee_name": member.name,
                        "role": role_name,
                        "department": member.department or "General",
                        "current_workload": round(workload_map.get(str(member.id), 0.0), 1),
                        "goals": [
                            {
                                "title": f"Own {focus_area}",
                                "description": f"Lead measurable improvements in {focus_area.lower()} for {role_name} responsibilities.",
                                "kpi": "Deliver 2 measurable improvements this quarter",
                                "weightage": 30,
                            },
                            {
                                "title": "Execution predictability",
                                "description": "Improve delivery reliability and reduce spillover risk.",
                                "kpi": "Maintain at least 90% committed delivery rate",
                                "weightage": 35,
                            },
                            {
                                "title": "Cross-team collaboration",
                                "description": "Partner with adjacent functions and remove at least one shared bottleneck.",
                                "kpi": "Resolve 1 cross-team dependency with documented impact",
                                "weightage": 35,
                            },
                        ],
                    }
                )

        prompt = prompts.team_goal_generation_prompt(
            manager_name=manager.name,
            team_structure=team_structure,
            employee_lines=employee_lines,
            objective=organization_objectives,
        )
        fallback = {"employees": [{"employee_id": row["employee_id"], "goals": row["goals"]} for row in fallback_employees]}
        payload = await self._execute(requester, "team_goal_allotment", prompt, fallback, db)

        generated = payload.get("employees") if isinstance(payload, dict) else None
        generated_map: dict[str, list[dict]] = {}
        if isinstance(generated, list):
            for item in generated:
                if not isinstance(item, dict):
                    continue
                key = str(item.get("employee_id", "")).strip()
                goals = item.get("goals", [])
                if key and isinstance(goals, list):
                    generated_map[key] = goals

        employees_output: list[dict] = []
        for row in fallback_employees:
            goals = generated_map.get(row["employee_id"], row["goals"])
            employees_output.append(
                {
                    **{k: v for k, v in row.items() if k != "goals"},
                    "goals": goals,
                }
            )

        return {
            "manager_id": str(manager.id),
            "team_structure": team_structure,
            "employees": employees_output,
        }

    async def summarize_checkin_transcript(self, user: User, meeting_transcript: str, db: AsyncSession) -> dict:
        prompt = prompts.checkin_summary_prompt(meeting_transcript)
        fallback = {
            "summary": "Check-in summary is temporarily unavailable.",
            "key_points": ["Transcript received"],
            "action_items": ["Retry summarization"],
        }
        return await self._execute(user, "checkin_summary", prompt, fallback, db)

    async def generate_feedback(self, user: User, manager_feedback: str, db: AsyncSession) -> dict:
        prompt = prompts.feedback_coaching_prompt(manager_feedback)
        fallback = {
            "improved_feedback": "Provide specific examples, expected outcomes, and a supportive tone.",
            "tone_score": 6,
            "suggested_version": "I appreciate your effort. Let us focus on clearer communication and timeline tracking in the next sprint.",
        }
        return await self._execute(user, "feedback_coaching", prompt, fallback, db)

    async def generate_performance_review(
        self,
        user: User,
        employee_goals: list[str],
        checkin_notes: list[str],
        manager_comments: str,
        db: AsyncSession,
    ) -> dict:
        prompt = prompts.performance_review_prompt(employee_goals, checkin_notes, manager_comments)
        fallback = {
            "performance_summary": "Performance review summary is currently unavailable.",
            "strengths": ["Consistent participation"],
            "weaknesses": ["Needs additional data for deeper assessment"],
            "growth_plan": ["Set clear quarterly milestones"],
        }
        return await self._execute(user, "performance_review", prompt, fallback, db)

    async def suggest_training_programs(self, user: User, department: str, skill_gaps: list[str], db: AsyncSession) -> dict:
        prompt = prompts.training_program_prompt(department, skill_gaps)
        fallback = {
            "programs": [
                {"name": "Core Skills Accelerator", "duration_weeks": 8, "outcome": "Improved baseline competencies"}
            ]
        }
        return await self._execute(user, "training_suggestions", prompt, fallback, db)

    async def suggest_career_growth(
        self,
        user: User,
        role: str,
        department: str,
        current_skills: list[str],
        target_role: str,
        db: AsyncSession,
    ) -> dict:
        prompt = prompts.career_growth_prompt(role, department, current_skills, target_role)
        fallback = {
            "growth_suggestions": ["Build leadership and domain depth"],
            "next_quarter_plan": ["Complete one stretch project"],
            "recommended_training": ["Advanced communication and decision-making"],
        }
        return await self._execute(user, "career_growth", prompt, fallback, db)

    async def decision_intelligence(self, user: User, context: str, questions: list[str], db: AsyncSession) -> dict:
        prompt = prompts.decision_intelligence_prompt(context, questions)
        fallback = {
            "insights": ["Insufficient AI context to generate robust insights"],
            "risks": ["Potential execution uncertainty"],
            "recommended_actions": ["Collect additional team and performance signals"],
        }
        return await self._execute(user, "decision_intelligence", prompt, fallback, db)

    async def chat(self, user: User, message: str, page: str | None, db: AsyncSession) -> dict:
        page_context = page or "general"
        prompt = (
            "You are an AI performance management copilot. "
            f"Current page: {page_context}. "
            f"User role: {user.role.value}. "
            f"User message: {message}. "
            "Return JSON only: {\"response\":\"...\",\"suggested_actions\":[\"...\"]}"
        )
        fallback = {
            "response": "I can help with goals, check-ins, ratings, and reviews. Please try a more specific question.",
            "suggested_actions": [
                "Review your pending goals",
                "Schedule your next check-in",
                "Open your review summary",
            ],
        }
        return await self._execute(user, "chat_assistant", prompt, fallback, db)
