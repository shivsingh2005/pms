"""
Goal Cluster and Employee Recommendation AI Services

Handles AI-driven goal cluster detection and team member recommendations
for universal goal assignment across all business functions.
"""

from uuid import UUID
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.gemini_client import GeminiClient, GeminiClientError
from app.ai import prompts
from app.models.user import User
from app.schemas.ai import (
    AIGoalClusterDetectRequest,
    AIGoalClusterDetectResponse,
    AIEmployeeRecommendRequest,
    AIEmployeeRecommendResponse,
    AINextActionRequest,
    AINextActionResponse,
)


class GoalClusterAIService:
    """AI services for detecting goal clusters and recommending employees."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    async def detect_goal_cluster(
        self,
        request: AIGoalClusterDetectRequest,
    ) -> AIGoalClusterDetectResponse:
        """
        Detect which universal goal cluster a goal belongs to.
        Works across all business functions, not just engineering.
        """
        if not self.client:
            raise ValueError("Gemini client not initialized")

        prompt = prompts.goal_cluster_detection_prompt(
            goal_title=request.goal_title,
            goal_description=request.goal_description,
            goal_kpi=request.goal_kpi,
            employee_role=request.employee_role,
            employee_department=request.employee_department,
            employee_function=request.employee_function,
        )

        try:
            response_text = await self.client.generate(prompt, max_tokens=500)
            
            # Parse JSON response
            result = json.loads(response_text)
            return AIGoalClusterDetectResponse(
                cluster_name=result.get("cluster_name", ""),
                cluster_category=result.get("cluster_category", ""),
                sub_category=result.get("sub_category", ""),
                applicable_functions=result.get("applicable_functions", []),
                goal_nature=result.get("goal_nature", "quantitative"),
                confidence=result.get("confidence", "Medium"),
                reasoning=result.get("reasoning", ""),
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback for parsing errors
            raise ValueError(f"Failed to parse cluster detection response: {e}")
        except GeminiClientError as e:
            raise ValueError(f"AI service error: {e}")

    async def recommend_employees_for_goal(
        self,
        request: AIEmployeeRecommendRequest,
    ) -> AIEmployeeRecommendResponse:
        """
        Recommend team members for a specific goal based on skills, workload,
        and historical performance. Does NOT rely on job title alone.
        """
        if not self.client:
            raise ValueError("Gemini client not initialized")

        # Convert team members to JSON for Gemini
        team_json = json.dumps(
            [
                {
                    "employee_id": str(member.employee_id),
                    "name": member.name,
                    "role": member.role,
                    "department": member.department,
                    "current_workload_percentage": member.current_workload_percentage,
                    "current_goals_count": member.current_goals_count,
                    "historical_performance_in_similar_goals": member.historical_performance_in_similar_goals,
                    "skills_demonstrated": member.skills_demonstrated,
                }
                for member in request.team_members
            ],
            indent=2,
        )

        prompt = prompts.employee_recommendation_prompt(
            goal_title=request.goal_title,
            goal_description=request.goal_description,
            goal_kpi=request.goal_kpi,
            goal_cluster=request.goal_cluster,
            goal_nature=request.goal_nature,
            team_members_json=team_json,
        )

        try:
            response_text = await self.client.generate(prompt, max_tokens=1000)
            result = json.loads(response_text)

            # Parse recommended employees
            recommended = [
                {
                    "employee_id": emp["employee_id"],
                    "name": emp["name"],
                    "role": emp.get("role", ""),
                    "match_score": emp.get("match_score", 0),
                    "match_reason": emp.get("match_reason", ""),
                    "current_workload": emp.get("current_workload", 0),
                    "workload_after_assignment": emp.get("workload_after_assignment", 0),
                    "fit_confidence": emp.get("fit_confidence", "Medium"),
                    "risk_flag": emp.get("risk_flag"),
                }
                for emp in result.get("recommended_employees", [])
            ]

            not_recommended = [
                {"employee_id": emp["employee_id"], "reason": emp.get("reason", "")}
                for emp in result.get("not_recommended", [])
            ]

            return AIEmployeeRecommendResponse(
                recommended_employees=recommended,
                not_recommended=not_recommended,
                cluster_insight=result.get("cluster_insight", ""),
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse recommendation response: {e}")
        except GeminiClientError as e:
            raise ValueError(f"AI service error: {e}")


class NextActionAIService:
    """Determines the user's next action based on their cycle state."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    async def determine_next_action(
        self,
        request: AINextActionRequest,
    ) -> AINextActionResponse:
        """
        Determine what action the user should take next in their performance cycle.
        Returns a single, clear next step based on cycle state.
        """
        # Apply deterministic logic first (no AI needed for most cases)
        
        if request.goals_count == 0:
            return AINextActionResponse(
                action="create_goals",
                message="Set your goals for this cycle to get started",
                priority="high",
                cta="Create Goals →",
                url="/employee/goals",
            )

        if request.goals_submitted_count == 0:
            return AINextActionResponse(
                action="submit_goals",
                message=f"Submit your {request.goals_count} goals to your manager for approval",
                priority="high",
                cta="Submit Goals →",
                url="/employee/goals",
            )

        if request.goals_approved_count == 0:
            return AINextActionResponse(
                action="wait_approval",
                message="Waiting for your manager to approve your goals",
                priority="medium",
                cta="View Goals",
                url="/employee/goals",
            )

        if request.days_since_last_checkin > 21 and request.checkins_count < 5:
            remaining = 5 - request.checkins_count
            return AINextActionResponse(
                action="submit_checkin",
                message=f"Check-in due — {remaining} remaining this quarter",
                priority="high",
                cta="Submit Check-in →",
                url="/employee/checkins",
            )

        if request.pending_approvals > 0:
            return AINextActionResponse(
                action="review_pending",
                message=f"You have {request.pending_approvals} pending approval(s) from your team",
                priority="high",
                cta="Review Now →",
                url="/manager/dashboard",
            )

        return AINextActionResponse(
            action="on_track",
            message="You're on track. Keep it up! 🎉",
            priority="low",
            cta="View Progress",
            url="/employee/dashboard",
        )
