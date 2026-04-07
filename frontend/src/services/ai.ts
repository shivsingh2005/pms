import { api } from "@/services/api";
import type {
  AIFeedbackCoachingResult,
  AIGrowthSuggestionResult,
  AIGoalGenerationResponse,
  AIQuarterlyUsage,
  EmployeeCascadeSuggestionRequest,
  EmployeeCascadeSuggestionResponse,
  TeamGoalGenerationResponse,
} from "@/types";

export const aiService = {
  async ask(message: string, page?: string) {
    const { data } = await api.post<{ response: string; suggested_actions?: string[] }>("/ai/chat", {
      message,
      page,
    });
    return data;
  },
  async summarizeCheckin(meetingTranscript: string) {
    const { data } = await api.post<{ summary: string; key_points: string[]; action_items: string[] }>(
      "/ai/checkins/summarize",
      { meeting_transcript: meetingTranscript },
    );
    return data;
  },
  async growthSuggestion(payload: { role: string; department: string; current_skills: string[]; target_role: string }) {
    const { data } = await api.post<AIGrowthSuggestionResult>("/ai/growth/suggest", payload);
    return data;
  },
  async generateGoalsForUser(payload: { user_id: string; organization_objectives?: string }) {
    const { data } = await api.post<AIGoalGenerationResponse>("/ai/goals/generate", payload);
    return data;
  },
  async generateTeamGoals(payload: { manager_id: string; organization_objectives?: string }) {
    const { data } = await api.post<TeamGoalGenerationResponse>("/ai/team-goals", payload);
    return data;
  },
  async getQuarterlyUsage() {
    const { data } = await api.get<AIQuarterlyUsage>("/ai/usage/quarterly");
    return data;
  },
  async coachFeedback(manager_feedback: string) {
    const { data } = await api.post<AIFeedbackCoachingResult>("/ai/feedback/coach", { manager_feedback });
    return data;
  },
  async suggestAopDistribution(payload: {
    total_target_value: number;
    target_unit: string;
    target_metric: string;
    managers: Array<{
      manager_id: string;
      manager_name: string;
      department?: string;
      team_size?: number;
      historical_performance?: number;
    }>;
  }) {
    const { data } = await api.post<{
      assignments: Array<{
        manager_id: string;
        manager_name: string;
        suggested_value: number;
        suggested_percentage: number;
        rationale: string;
      }>;
      distribution_rationale: string;
      balance_score: number;
    }>("/ai/aop/suggest-distribution", payload);
    return data;
  },
  async suggestEmployeeSplit(payload: EmployeeCascadeSuggestionRequest) {
    const { data } = await api.post<EmployeeCascadeSuggestionResponse>("/ai/goal-cascade/suggest-employee-split", payload);
    return data;
  },
};
