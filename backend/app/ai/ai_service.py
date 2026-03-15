from datetime import datetime, timezone
from uuid import UUID
from app.ai.gemini_client import GeminiClient, GeminiClientError
from app.ai import prompts
from app.models.ai_usage_log import AIUsageLog
from app.models.enums import UserRole
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
