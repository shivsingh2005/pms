import { api } from "@/services/api";
import type {
  AOPManagerAssignment,
  AOPProgress,
  CascadedEmployeeGoal,
  CascadedManagerGoal,
  GoalLineageImpact,
  LeadershipAOPTarget,
} from "@/types";

export const leadershipGoalsService = {
  async listAopTargets() {
    const { data } = await api.get<LeadershipAOPTarget[]>("/leadership/aop");
    return data;
  },

  async createAopTarget(payload: {
    title: string;
    description?: string;
    total_target_value: number;
    target_unit: string;
    target_metric: string;
    year: number;
    quarter?: number;
    department?: string;
  }) {
    const { data } = await api.post<LeadershipAOPTarget>("/leadership/aop", payload);
    return data;
  },

  async updateAopTarget(aopId: string, payload: Partial<{
    title: string;
    description: string;
    total_target_value: number;
    target_unit: string;
    target_metric: string;
    year: number;
    quarter: number;
    department: string;
    status: string;
  }>) {
    const { data } = await api.patch<LeadershipAOPTarget>(`/leadership/aop/${aopId}`, payload);
    return data;
  },

  async listAssignments(aopId: string) {
    const { data } = await api.get<AOPManagerAssignment[]>(`/leadership/aop/${aopId}/assignments`);
    return data;
  },

  async assignManagers(aopId: string, assignments: Array<{ manager_id: string; target_value: number; target_percentage: number }>) {
    const { data } = await api.post<AOPManagerAssignment[]>(`/leadership/aop/${aopId}/assign-managers`, { assignments });
    return data;
  },

  async getProgress(aopId: string) {
    const { data } = await api.get<AOPProgress>(`/leadership/aop/${aopId}/progress`);
    return data;
  },

  async suggestAopDistribution(payload: {
    total_target_value: number;
    target_unit: string;
    target_metric: string;
    managers: Array<{ manager_id: string; manager_name: string; department?: string; team_size?: number; historical_performance?: number }>;
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
  
  async listManagerCascadedGoals() {
    const { data } = await api.get<CascadedManagerGoal[]>("/manager/cascaded-goals");
    return data;
  },

  async acknowledgeManagerGoal(goalId: string) {
    const { data } = await api.post<{ acknowledged: boolean; goal_id?: string; reason?: string }>(`/manager/cascaded-goals/${goalId}/acknowledge`);
    return data;
  },

  async cascadeManagerGoalToTeam(
    goalId: string,
    payload: { employee_assignments: Array<{ employee_id: string; target_value: number; target_percentage: number }> },
  ) {
    const { data } = await api.post<{ count: number; created_goals: string[]; reason?: string }>(`/manager/cascaded-goals/${goalId}/cascade-to-team`, payload);
    return data;
  },

  async listEmployeeCascadedGoals() {
    const { data } = await api.get<CascadedEmployeeGoal[]>("/employee/goals/cascaded");
    return data;
  },

  async acknowledgeEmployeeGoal(goalId: string) {
    const { data } = await api.post<{ acknowledged: boolean; goal_id?: string }>(`/employee/goals/${goalId}/acknowledge`);
    return data;
  },

  async getEmployeeLineage(goalId: string) {
    const { data } = await api.get<GoalLineageImpact>(`/employee/goals/${goalId}/lineage`);
    return data;
  },
};
