import { api } from "@/services/api";
import type { DashboardNextAction } from "@/types";
import { useSessionStore } from "@/store/useSessionStore";

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

type EmployeeDashboardOverviewResponse = {
  employee_id: string;
  goals_count: number;
  avg_goal_progress: number;
  checkins_count: number;
  avg_rating: number;
};

function employeeFallbackNextAction(data?: EmployeeDashboardOverviewResponse): DashboardNextAction {
  const goalsCount = Number(data?.goals_count ?? 0);
  const checkinsCount = Number(data?.checkins_count ?? 0);

  if (goalsCount === 0) {
    return {
      title: "Create your first goal",
      detail: "Define one measurable goal to start this cycle.",
      action_url: "/goals",
      action_label: "Create Goal",
      level: "warning",
    };
  }

  if (checkinsCount === 0) {
    return {
      title: "Submit your first check-in",
      detail: "Share progress so your manager can review your momentum.",
      action_url: "/checkins",
      action_label: "Open Check-ins",
      level: "warning",
    };
  }

  return {
    title: "You are on track",
    detail: "Keep updating goals and check-ins to maintain momentum.",
    action_url: "/employee/dashboard",
    action_label: "View Dashboard",
    level: "info",
  };
}

export const dashboardService = {
  async getOverview() {
    const { data } = await api.get<DashboardOverview>("/dashboard/overview");
    return data;
  },
  async getEmployeeDashboard() {
    const { data } = await api.get<EmployeeDashboardOverviewResponse>("/employee-dashboard/overview");
    return {
      progress: Number(data.avg_goal_progress ?? 0),
      completed_goals: 0,
      active_goals: Number(data.goals_count ?? 0),
      checkins_count: Number(data.checkins_count ?? 0),
      last_checkin: null,
      consistency_percent: Number(data.avg_goal_progress ?? 0),
      manager_name: null,
      manager_email: null,
      manager_title: null,
      review_readiness: Number(data.avg_rating ?? 0) >= 3.5 ? "High" : Number(data.avg_rating ?? 0) >= 2.5 ? "Medium" : "Low",
      checkin_status: Number(data.checkins_count ?? 0) > 0 ? "On Track" : "Missed",
      trend: [],
      consistency: [],
    } as EmployeeDashboardData;
  },
  async getNextAction() {
    try {
      const { data } = await api.get<DashboardNextAction>("/dashboard/next-action", {
        ...( { skipErrorToast: true } as object),
      });
      return data;
    } catch {
      const role = useSessionStore.getState().user?.role;
      if (role === "employee") {
        try {
          const { data } = await api.get<EmployeeDashboardOverviewResponse>("/employee-dashboard/overview", {
            ...( { skipErrorToast: true } as object),
          });
          return employeeFallbackNextAction(data);
        } catch {
          return employeeFallbackNextAction();
        }
      }

      return {
        title: "Stay aligned with your cycle",
        detail: "Review your dashboard and complete pending actions.",
        action_url: "/manager/dashboard",
        action_label: "Open Dashboard",
        level: "info",
      };
    }
  },
};
