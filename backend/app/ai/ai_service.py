from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict
from sqlalchemy import func, select
from app.ai.gemini_client import GeminiClient, GeminiClientError
from app.ai import prompts
from app.models.goal import Goal
from app.models.annual_operating_plan import AnnualOperatingPlan
from app.models.ai_usage_log import AIUsageLog
from app.models.enums import GoalStatus, UserRole
from app.models.kpi_library import KPILibrary
from app.models.user import User
from app.schemas.ai import AOPDistributionSuggestRequest, EmployeeCascadeSuggestRequest
from sqlalchemy.ext.asyncio import AsyncSession


class AIService:
    FEATURE_ACCESS: dict[str, set[UserRole]] = {
        "chat_assistant": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership},
        "goal_suggestions": {UserRole.employee, UserRole.hr, UserRole.leadership},
        "career_growth": {UserRole.employee, UserRole.hr, UserRole.leadership},
        "checkin_summary": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership},
        "rating_suggestion": {UserRole.manager, UserRole.hr, UserRole.leadership},
        "performance_review": {UserRole.manager, UserRole.hr, UserRole.leadership},
        "feedback_coaching": {UserRole.manager, UserRole.hr, UserRole.leadership},
        "training_suggestions": {UserRole.hr, UserRole.leadership},
        "decision_intelligence": {UserRole.manager, UserRole.hr, UserRole.leadership},
        "role_based_goal_generation": {UserRole.employee, UserRole.manager, UserRole.hr, UserRole.leadership},
        "team_goal_allotment": {UserRole.manager, UserRole.hr, UserRole.leadership},
        "aop_distribution": {UserRole.hr, UserRole.leadership},
        "employee_split": {UserRole.manager, UserRole.hr, UserRole.leadership},
    }

    ROLE_FOCUS_AREAS: dict[str, list[str]] = {
        "backend": ["API performance", "Database optimization", "Service security", "Automated testing", "Developer experience"],
        "frontend": ["Core web vitals", "UX accessibility", "Design system quality", "Automated UI testing", "Frontend observability"],
        "devops": ["Deployment reliability", "Cost optimization", "Monitoring quality", "Infrastructure security", "Release automation"],
        "qa": ["Regression coverage", "Test automation", "Defect prevention", "Performance testing", "Release quality gates"],
        "data": ["Data quality", "Pipeline reliability", "Model performance", "Experiment cadence", "Stakeholder reporting"],
        "product": ["Roadmap execution", "Discovery quality", "Cross-team alignment", "Outcome measurement", "Customer feedback loops"],
    }

    FEATURE_QUARTER_LIMITS: dict[str, int] = {
        "chat_assistant": 60,
        "goal_suggestions": 24,
        "career_growth": 24,
        "checkin_summary": 40,
        "rating_suggestion": 24,
        "performance_review": 20,
        "feedback_coaching": 20,
        "training_suggestions": 16,
        "decision_intelligence": 20,
        "role_based_goal_generation": 24,
        "team_goal_allotment": 16,
        "aop_distribution": 2,
        "employee_split": 3,
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

    @staticmethod
    def _role_intelligence(title: str | None, department: str | None) -> list[str]:
        text = f"{title or ''} {department or ''}".lower()
        if any(token in text for token in ("frontend", "ui", "react", "design")):
            return [
                "Benchmark: include performance and accessibility outcomes.",
                "Benchmark: include one cross-functional product collaboration objective.",
            ]
        if any(token in text for token in ("backend", "api", "platform", "database")):
            return [
                "Benchmark: include reliability, security, and latency improvements.",
                "Benchmark: include measurable service-level outcomes.",
            ]
        if any(token in text for token in ("hr", "people", "talent")):
            return [
                "Benchmark: include retention, engagement, or capability development outcomes.",
                "Benchmark: include policy quality and employee experience metrics.",
            ]
        return ["Benchmark: include measurable execution, quality, and collaboration outcomes."]

    async def _build_grounding_context(
        self,
        organization_id: UUID,
        role_title: str | None,
        department: str | None,
        db: AsyncSession,
    ) -> str | None:
        current_year = datetime.now(timezone.utc).year

        aop_result = await db.execute(
            select(AnnualOperatingPlan)
            .where(
                AnnualOperatingPlan.organization_id == organization_id,
                AnnualOperatingPlan.year == current_year,
            )
            .order_by(AnnualOperatingPlan.created_at.desc())
            .limit(5)
        )
        aop_rows = list(aop_result.scalars().all())

        kpi_stmt = select(KPILibrary)
        if role_title:
            kpi_stmt = kpi_stmt.where(KPILibrary.role == role_title)
        if department:
            kpi_stmt = kpi_stmt.where((KPILibrary.department == department) | (KPILibrary.department.is_(None)))

        kpi_result = await db.execute(kpi_stmt.order_by(KPILibrary.updated_at.desc()).limit(6))
        kpi_rows = list(kpi_result.scalars().all())

        if not aop_rows and not kpi_rows:
            return None

        parts: list[str] = []
        if aop_rows:
            lines = [f"{row.year}-{row.department or 'org'}: {row.objective}" for row in aop_rows]
            parts.append("AOP:\n" + "\n".join(f"- {line}" for line in lines))

        if kpi_rows:
            lines = [f"{row.goal_title} (KPI: {row.suggested_kpi}; wt={row.suggested_weight})" for row in kpi_rows]
            parts.append("KPI Templates:\n" + "\n".join(f"- {line}" for line in lines))

        return "\n\n".join(parts)

    async def _build_allotted_goals_context(self, target_user_id: UUID, db: AsyncSession) -> str | None:
        result = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == target_user_id,
                Goal.assigned_by.is_not(None),
                Goal.status != GoalStatus.rejected,
            )
            .order_by(Goal.created_at.desc())
            .limit(8)
        )
        allotted_goals = list(result.scalars().all())

        if not allotted_goals:
            return None

        lines: list[str] = []
        for goal in allotted_goals:
            description = (goal.description or "").strip()
            compact_description = " ".join(description.split())
            if len(compact_description) > 180:
                compact_description = f"{compact_description[:177]}..."

            lines.append(
                f"- {goal.title} | framework={goal.framework.value} | weight={round(float(goal.weightage), 1)} | progress={round(float(goal.progress), 1)} | desc={compact_description or 'n/a'}"
            )

        return "Manager-allotted goals for this employee:\n" + "\n".join(lines)

    @staticmethod
    def _allotted_goals_seed_recommendations(allotted_goals: list[Goal], focus_area: str, department: str) -> list[dict]:
        if not allotted_goals:
            return []

        seeds: list[dict] = []
        for goal in allotted_goals[:4]:
            base_title = (goal.title or "Execution Goal").strip()
            base_description = (goal.description or "").strip()

            transformed_title = f"Advance: {base_title}"
            transformed_description = (
                f"Build on manager-allotted goal '{base_title}' with measurable execution outcomes"
                + (f". Context: {base_description[:180]}" if base_description else ".")
            )
            transformed_kpi = f"Deliver agreed milestone for '{base_title}' and report weekly progress with measurable impact"

            seeds.append(
                {
                    "title": transformed_title,
                    "description": transformed_description,
                    "kpi": transformed_kpi,
                    "weightage": max(10.0, min(float(goal.weightage or 25.0), 40.0)),
                }
            )

        # If fewer than 4 allotted goals exist, add one coverage goal anchored to focus area.
        while len(seeds) < 4:
            seeds.append(
                {
                    "title": f"Support {focus_area}",
                    "description": f"Complement manager-allotted goals by improving {focus_area.lower()} outcomes in {department}.",
                    "kpi": "Deliver at least 2 measurable improvements that accelerate allotted-goal outcomes",
                    "weightage": 25.0,
                }
            )

        # Normalize top 4 weights to total exactly 100.
        top_four = seeds[:4]
        total = sum(item["weightage"] for item in top_four) or 100.0
        normalized: list[dict] = []
        running = 0.0
        for index, item in enumerate(top_four):
            if index < 3:
                weight = round((item["weightage"] * 100.0) / total, 1)
                running += weight
            else:
                weight = round(100.0 - running, 1)

            normalized.append(
                {
                    "title": item["title"],
                    "description": item["description"],
                    "kpi": item["kpi"],
                    "weightage": weight,
                }
            )

        return normalized

    async def _check_rbac(self, feature_name: str, user: User) -> None:
        allowed = self.FEATURE_ACCESS.get(feature_name, set())
        if user.role not in allowed:
            raise PermissionError("Role is not allowed for this AI feature")

    async def _feature_usage_count(self, user_id: UUID, feature_name: str, quarter: int, year: int, db: AsyncSession) -> int:
        start_month = ((quarter - 1) * 3) + 1
        end_month = start_month + 2

        result = await db.execute(
            select(func.count(AIUsageLog.id)).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.feature_name == feature_name,
                func.extract("year", AIUsageLog.created_at) == year,
                func.extract("month", AIUsageLog.created_at).between(start_month, end_month),
            )
        )
        count = result.scalar() or 0
        return int(count)

    async def _enforce_quarter_limit(self, user: User, feature_name: str, db: AsyncSession) -> None:
        quarter, year = self._quarter_now()
        feature_limit = self.FEATURE_QUARTER_LIMITS.get(feature_name, 12)
        used = await self._feature_usage_count(user.id, feature_name, quarter, year, db)

        if used >= feature_limit:
            raise RuntimeError(f"Quarterly AI usage cap reached for {feature_name}")

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
        await self._enforce_quarter_limit(user, feature_name, db)

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

    async def get_quarterly_usage(self, user: User, db: AsyncSession) -> dict:
        quarter, year = self._quarter_now()
        features: list[dict] = []
        for feature_name, limit in self.FEATURE_QUARTER_LIMITS.items():
            used = await self._feature_usage_count(user.id, feature_name, quarter, year, db)
            features.append(
                {
                    "feature_name": feature_name,
                    "used": used,
                    "limit": limit,
                    "remaining": max(limit - used, 0),
                }
            )

        return {
            "quarter": quarter,
            "year": year,
            "features": features,
        }

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

    @staticmethod
    def _sanitize_goal_item(goal: object) -> dict | None:
        if not isinstance(goal, dict):
            return None

        title = str(goal.get("title", "")).strip()
        description = str(goal.get("description", "")).strip()
        kpi = str(goal.get("kpi", "")).strip()
        if not title or not description or not kpi:
            return None

        try:
            weightage = float(goal.get("weightage", 0))
        except (TypeError, ValueError):
            return None

        if weightage <= 0:
            return None

        return {
            "title": title,
            "description": description,
            "kpi": kpi,
            "weightage": weightage,
        }

    @classmethod
    def _sanitize_goals(cls, goals: object) -> list[dict]:
        if not isinstance(goals, list):
            return []

        sanitized: list[dict] = []
        for goal in goals:
            parsed = cls._sanitize_goal_item(goal)
            if parsed is not None:
                sanitized.append(parsed)
        return sanitized

    @staticmethod
    def _goals_grounded_in_allotted(generated_goals: list[dict], allotted_goals: list[Goal]) -> bool:
        if not generated_goals or not allotted_goals:
            return False

        allotted_tokens: set[str] = set()
        for goal in allotted_goals:
            for token in (goal.title or "").lower().replace("-", " ").split():
                cleaned = "".join(ch for ch in token if ch.isalnum())
                if len(cleaned) >= 4:
                    allotted_tokens.add(cleaned)

        if not allotted_tokens:
            return False

        for goal in generated_goals:
            text = f"{goal.get('title', '')} {goal.get('description', '')}".lower()
            if any(token in text for token in allotted_tokens):
                return True

        return False

    async def generate_role_based_goals(
        self,
        requester: User,
        target_user_id: str,
        organization_objectives: str | None,
        db: AsyncSession,
        grounding_context: str | None = None,
        role_intelligence: list[str] | None = None,
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

        if target_user.organization_id != requester.organization_id:
            raise PermissionError("Cross-organization access is not allowed")

        title = (getattr(target_user, "title", None) or "Individual Contributor").strip()
        department = (getattr(target_user, "department", None) or "General").strip()

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

        computed_grounding = grounding_context
        if computed_grounding is None:
            try:
                computed_grounding = await self._build_grounding_context(
                    organization_id=target_user.organization_id,
                    role_title=title,
                    department=department,
                    db=db,
                )
            except Exception:
                computed_grounding = None

        computed_role_intelligence = role_intelligence or self._role_intelligence(title, department)
        allotted_goals_context = await self._build_allotted_goals_context(target_user.id, db)
        allotted_goals_result = await db.execute(
            select(Goal)
            .where(
                Goal.user_id == target_user.id,
                Goal.assigned_by.is_not(None),
                Goal.status != GoalStatus.rejected,
            )
            .order_by(Goal.created_at.desc())
            .limit(8)
        )
        allotted_goals = list(allotted_goals_result.scalars().all())
        allotted_seed_goals = self._allotted_goals_seed_recommendations(allotted_goals, focus_area, department)

        prompt = prompts.role_based_goal_generation_prompt(
            role_title=title,
            role=target_user.role.value,
            department=department,
            team_size=team_size,
            member_index=member_index,
            focus_area=focus_area,
            objective=organization_objectives,
            grounding_context=computed_grounding,
            role_intelligence=computed_role_intelligence,
            allotted_goals_context=allotted_goals_context,
        )

        fallback = {
            "goals": allotted_seed_goals
            or [
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

        sanitized_goals = self._sanitize_goals(payload.get("goals") if isinstance(payload, dict) else None)
        if allotted_seed_goals and not self._goals_grounded_in_allotted(sanitized_goals, allotted_goals):
            sanitized_goals = []

        return {
            "user_id": str(target_user.id),
            "title": title,
            "department": department,
            "team_size": team_size,
            "focus_area": focus_area,
            "goals": sanitized_goals or fallback["goals"],
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
        grounding_context: str | None = None,
        role_intelligence: list[str] | None = None,
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

        if requester.organization_id != manager.organization_id:
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

        computed_grounding = grounding_context
        if computed_grounding is None:
            try:
                computed_grounding = await self._build_grounding_context(
                    organization_id=manager.organization_id,
                    role_title=getattr(manager, "title", None),
                    department=getattr(manager, "department", None),
                    db=db,
                )
            except Exception:
                computed_grounding = None

        computed_role_intelligence = role_intelligence or self._role_intelligence(
            getattr(manager, "title", None),
            getattr(manager, "department", None),
        )

        prompt = prompts.team_goal_generation_prompt(
            manager_name=manager.name,
            team_structure=team_structure,
            employee_lines=employee_lines,
            objective=organization_objectives,
            grounding_context=computed_grounding,
            role_intelligence=computed_role_intelligence,
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
                goals = self._sanitize_goals(item.get("goals"))
                if key and goals:
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

    async def suggest_rating(
        self,
        user: User,
        overall_progress: int,
        confidence_level: int,
        blockers: str | None,
        achievements: str | None,
        db: AsyncSession,
    ) -> dict:
        prompt = prompts.rating_suggestion_prompt(
            overall_progress=overall_progress,
            confidence_level=confidence_level,
            blockers=blockers,
            achievements=achievements,
        )

        raw = 1.0 + (max(min(overall_progress, 100), 0) / 100.0) * 3.0 + (confidence_level - 3) * 0.2
        if (blockers or "").strip():
            raw -= 0.5
        if (achievements or "").strip():
            raw += 0.2

        fallback_rating = int(round(max(1.0, min(raw, 5.0))))
        fallback = {
            "suggested_rating": fallback_rating,
            "confidence": 0.72,
            "rationale": [
                f"Overall progress is {overall_progress}%.",
                f"Confidence level reported as {confidence_level}/5.",
                "Blockers and achievements were considered for recommendation.",
            ],
        }
        return await self._execute(user, "rating_suggestion", prompt, fallback, db)

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

    async def suggest_aop_distribution(
        self,
        user: User,
        payload: AOPDistributionSuggestRequest,
        db: AsyncSession,
    ) -> dict:
        managers = payload.managers or []
        if not managers:
            return {"assignments": [], "distribution_rationale": "No managers supplied", "balance_score": 0}

        manager_lines = "\n".join(
            f"- {row.manager_id} | {row.manager_name} | dept={row.department or 'General'} | team_size={row.team_size or 0} | perf={row.historical_performance or 0}"
            for row in managers
        )
        prompt = (
            f"Suggest how to distribute {payload.total_target_value} {payload.target_unit} {payload.target_metric} across managers.\n"
            f"Managers:\n{manager_lines}\n"
            "Return JSON {assignments:[{manager_id,manager_name,suggested_value,suggested_percentage,rationale}],distribution_rationale,balance_score}"
        )

        total_weight = 0.0
        weighted_rows = []
        for row in managers:
            weight = float((row.team_size or 1) * 0.7 + (row.historical_performance or 50) * 0.3)
            total_weight += max(weight, 1.0)
            weighted_rows.append((row, max(weight, 1.0)))

        assignments = []
        running = 0.0
        for index, (row, weight) in enumerate(weighted_rows):
            if index < len(weighted_rows) - 1:
                pct = round(weight * 100.0 / total_weight, 1)
                running += pct
            else:
                pct = round(100.0 - running, 1)
            value = round(payload.total_target_value * pct / 100.0, 2)
            assignments.append(
                {
                    "manager_id": row.manager_id,
                    "manager_name": row.manager_name,
                    "suggested_value": value,
                    "suggested_percentage": pct,
                    "rationale": "Balanced by team size and historical performance",
                }
            )

        fallback = {
            "assignments": assignments,
            "distribution_rationale": "Balanced by team capacity and historical performance",
            "balance_score": 82,
        }
        return await self._execute(user, "aop_distribution", prompt, fallback, db)

    async def suggest_employee_split(
        self,
        user: User,
        payload: EmployeeCascadeSuggestRequest,
        db: AsyncSession,
    ) -> dict:
        employees = payload.employees or []
        if not employees:
            return {"assignments": [], "total_check": 0, "warnings": ["No employees supplied"]}

        employee_lines = "\n".join(
            f"- {row.employee_id} | {row.name} | role={row.role} | workload={row.current_workload_percentage} | perf={row.historical_performance_score or 0}"
            for row in employees
        )
        prompt = (
            f"Suggest split for {payload.total_target_value} {payload.target_unit} {payload.target_metric} across team.\n"
            f"Manager={payload.manager_name}\nEmployees:\n{employee_lines}\n"
            "Return JSON {assignments:[{employee_id,suggested_value,suggested_percentage,rationale,workload_after}],total_check,warnings}"
        )

        weights = []
        total_weight = 0.0
        for row in employees:
            capacity = max(5.0, 100.0 - row.current_workload_percentage)
            perf = row.historical_performance_score or 50.0
            weight = capacity * 0.6 + perf * 0.4
            weight = max(weight, 1.0)
            total_weight += weight
            weights.append((row, weight))

        assignments = []
        warnings: list[str] = []
        running = 0.0
        for idx, (row, weight) in enumerate(weights):
            if idx < len(weights) - 1:
                pct = round(weight * 100.0 / total_weight, 1)
                running += pct
            else:
                pct = round(100.0 - running, 1)
            value = round(payload.total_target_value * pct / 100.0, 2)
            workload_after = round(min(100.0, row.current_workload_percentage + pct), 1)
            if workload_after > 80:
                warnings.append(f"{row.name} may be overloaded at {workload_after}%")
            assignments.append(
                {
                    "employee_id": row.employee_id,
                    "suggested_value": value,
                    "suggested_percentage": pct,
                    "rationale": "Distributed by available capacity and performance context",
                    "workload_after": workload_after,
                }
            )

        fallback = {
            "assignments": assignments,
            "total_check": round(sum(item["suggested_percentage"] for item in assignments), 1),
            "warnings": warnings,
        }
        return await self._execute(user, "employee_split", prompt, fallback, db)
