import { api } from "@/services/api";
import type { Goal } from "@/types";

interface CreateGoalPayload {
  title: string;
  description?: string | null;
  weightage: number;
  progress: number;
  framework: "OKR" | "MBO" | "Hybrid";
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
};
