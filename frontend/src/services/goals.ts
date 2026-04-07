import { api } from "@/services/api";
import type {
  GoalChangeLog,
  GoalCascadeChildPayload,
  GoalCascadeResult,
  Goal,
  GoalAssignmentCandidate,
  GoalAssignmentRecommendationsPayload,
  GoalDriftInsight,
  GoalLineage,
  GoalAssignmentSingleResult,
} from "@/types";

interface CreateGoalPayload {
  title: string;
  description?: string | null;
  weightage: number;
  progress: number;
  framework: "OKR" | "MBO" | "Hybrid";
}

interface GoalAssignItem {
  goal_id?: string;
  title: string;
  description?: string | null;
  kpi?: string | null;
  weightage: number;
  framework: "OKR" | "MBO" | "Hybrid";
  progress: number;
}

interface GoalAssignPayload {
  employee_id: string;
  approve?: boolean;
  reject?: boolean;
  is_ai_generated?: boolean;
  goals: GoalAssignItem[];
}

interface GoalAssignSinglePayload {
  employee_id: string;
  role: "frontend" | "backend" | "others";
  title: string;
  description?: string | null;
  kpi?: string | null;
  weightage: number;
  framework: "OKR" | "MBO" | "Hybrid";
  progress: number;
  approve?: boolean;
  allow_overload?: boolean;
  is_ai_generated?: boolean;
}

export const goalsService = {
  async getGoals() {
    const { data } = await api.get<Goal[]>("/goals");
    return data;
  },
  async createGoal(payload: CreateGoalPayload) {
    const { data } = await api.post<Goal>("/goals", payload);
    return data;
  },
  async updateGoal(id: string, payload: Partial<CreateGoalPayload>) {
    const { data } = await api.patch<Goal>(`/goals/${id}`, payload);
    return data;
  },
  async submitGoal(id: string) {
    const { data } = await api.post<Goal>(`/goals/${id}/submit`);
    return data;
  },
  async approveGoal(id: string) {
    const { data } = await api.post<Goal>(`/goals/${id}/approve`);
    return data;
  },
  async rejectGoal(id: string) {
    const { data } = await api.post<Goal>(`/goals/${id}/reject`);
    return data;
  },
  async assignGoals(payload: GoalAssignPayload) {
    const { data } = await api.post<Goal[]>("/goals/assign", payload);
    return data;
  },
  async getAssignmentRecommendations(payload: { organization_objectives?: string }) {
    const { data } = await api.post<GoalAssignmentRecommendationsPayload>(
      "/goals/assignment/recommendations",
      payload,
    );
    return data;
  },
  async getAssignmentCandidates(role: "frontend" | "backend" | "others") {
    const { data } = await api.get<GoalAssignmentCandidate[]>(`/goals/assignment/candidates/${role}`);
    return data;
  },
  async assignSingleGoal(payload: GoalAssignSinglePayload) {
    const { data } = await api.post<GoalAssignmentSingleResult>("/goals/assignment/one", payload);
    return data;
  },
  async cascadeGoal(payload: { parent_goal_id: string; normalize_weights?: boolean; children: GoalCascadeChildPayload[] }) {
    const { data } = await api.post<GoalCascadeResult>("/goals/cascade", payload);
    return data;
  },
  async getGoalLineage(goalId: string) {
    const { data } = await api.get<GoalLineage>(`/goals/lineage/${goalId}`);
    return data;
  },
  async getGoalChanges(goalId: string) {
    const { data } = await api.get<GoalChangeLog[]>(`/goals/changes/${goalId}`);
    return data;
  },
  async getGoalDriftInsights() {
    const { data } = await api.get<GoalDriftInsight[]>("/goals/insights/drift");
    return data;
  },
};
