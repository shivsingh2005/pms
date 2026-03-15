import { create } from "zustand";
import type { Goal } from "@/types";
import { goalsService } from "@/services/goals";

interface GoalsState {
  goals: Goal[];
  loading: boolean;
  fetchGoals: () => Promise<void>;
  addGoal: (payload: {
    title: string;
    description?: string;
    weightage: number;
    progress: number;
    framework: "OKR" | "MBO" | "Hybrid";
  }) => Promise<void>;
  updateGoal: (id: string, payload: Partial<Goal>) => Promise<void>;
  submitGoal: (id: string) => Promise<void>;
}

export const useGoalsStore = create<GoalsState>((set, get) => ({
  goals: [],
  loading: false,
  fetchGoals: async () => {
    set({ loading: true });
    const goals = await goalsService.getGoals();
    set({ goals, loading: false });
  },
  addGoal: async (payload) => {
    await goalsService.createGoal(payload);
    await get().fetchGoals();
  },
  updateGoal: async (id, payload) => {
    await goalsService.updateGoal(id, payload);
    await get().fetchGoals();
  },
  submitGoal: async (id) => {
    await goalsService.submitGoal(id);
    await get().fetchGoals();
  },
}));
