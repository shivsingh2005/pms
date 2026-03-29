import { api } from "@/services/api";
import type { Goal } from "@/types";

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
};
