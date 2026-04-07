import { api } from "@/services/api";
import type { DashboardNextAction } from "@/types";

export interface DashboardOverview {
  role: string;
  kpi: {
    goals_completed?: number;
    total_goals?: number;
    consistency?: number;
    review_readiness?: string;
    peer_signals?: number;
    team_goals?: number;
    at_risk_goals?: number;
    active_reports?: number;
    org_health?: number;
    cycle_completion?: number;
    risk_flags?: number;
    leadership_signals?: number;
  };
  trend: { name: string; score: number }[];
  velocity: { name: string; score: number }[];
  distribution: { name: string; value: number }[];
  heatmap: number[];
  stack_ranking: { name: string; score: number; trend: "up" | "down" | "flat" }[];
  insights: {
    primary: string;
    secondary: string;
  };
}

export interface EmployeeDashboardData {
  progress: number;
  completed_goals: number;
  active_goals: number;
  checkins_count: number;
  last_checkin: string | null;
  consistency_percent: number;
  manager_name: string | null;
  manager_email: string | null;
  manager_title: string | null;
  review_readiness: string;
  checkin_status: "On Track" | "Missed";
  trend: { week: string; value: number }[];
  consistency: { week: string; value: number }[];
}

export const dashboardService = {
  async getOverview() {
    const { data } = await api.get<DashboardOverview>("/dashboard/overview");
    return data;
  },
  async getEmployeeDashboard() {
    const { data } = await api.get<EmployeeDashboardData>("/employee/dashboard");
    return data;
  },
  async getNextAction() {
    const { data } = await api.get<DashboardNextAction>("/dashboard/next-action", {
      ...( { skipErrorToast: true } as object),
    });
    return data;
  },
};
