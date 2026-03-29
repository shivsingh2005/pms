import { api } from "@/services/api";
import type { AIGoalGenerationResponse, TeamGoalGenerationResponse } from "@/types";

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
    const { data } = await api.post("/ai/growth/suggest", payload);
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
};
