"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { safeArray, safeNumber } from "@/lib/safeData";

type ManagerDashboardData = {
  team_size: number;
  avg_performance: number;
  consistency: number;
  at_risk: number;
  pending_approvals: number;
  completed_goals?: number;
  insights?: string[];
  team: unknown[];
  stack_ranking: unknown[];
  rag_heatmap: unknown[];
  performance_trend: unknown[];
  rating_distribution: unknown[];
  checkin_status: unknown[];
  top_performers: unknown[];
  low_performers: unknown[];
};

type EmployeeDashboardData = {
  overall_progress: number;
  goals_count: number;
  checkins_used: number;
  checkins_total: number;
  avg_rating: number | null;
  band: string | null;
  manager_name: string | null;
  manager_email: string | null;
  manager_title: string | null;
  timeline: { nodes: unknown[] };
  goals_preview: unknown[];
  banner: unknown;
};

type HrDashboardData = {
  total_employees: number;
  avg_performance: number;
  at_risk: number;
  need_training: number;
  alerts: unknown[];
  training_heatmap: unknown[];
  quick_stats: {
    checkin_rate: number;
    approval_rate: number;
    rating_rate: number;
    meeting_count: number;
  };
};

type LeadershipDashboardData = {
  org_performance: number;
  aop_achievement: number;
  high_performers: number;
  at_risk: number;
  aop_progress: {
    total: number;
    achieved: number;
    by_unit: unknown[];
  };
  talent_snapshot: {
    top_performers: unknown[];
    at_risk: unknown[];
  };
};

export const DEFAULT_MANAGER_DATA: ManagerDashboardData = {
  team_size: 0,
  avg_performance: 0,
  consistency: 0,
  at_risk: 0,
  pending_approvals: 0,
  completed_goals: 0,
  insights: [],
  team: [],
  stack_ranking: [],
  rag_heatmap: [],
  performance_trend: [],
  rating_distribution: [],
  checkin_status: [],
  top_performers: [],
  low_performers: [],
};

export const DEFAULT_EMPLOYEE_DATA: EmployeeDashboardData = {
  overall_progress: 0,
  goals_count: 0,
  checkins_used: 0,
  checkins_total: 5,
  avg_rating: null,
  band: null,
  manager_name: null,
  manager_email: null,
  manager_title: null,
  timeline: { nodes: [] },
  goals_preview: [],
  banner: null,
};

export const DEFAULT_HR_DATA: HrDashboardData = {
  total_employees: 0,
  avg_performance: 0,
  at_risk: 0,
  need_training: 0,
  alerts: [],
  training_heatmap: [],
  quick_stats: {
    checkin_rate: 0,
    approval_rate: 0,
    rating_rate: 0,
    meeting_count: 0,
  },
};

export const DEFAULT_LEADERSHIP_DATA: LeadershipDashboardData = {
  org_performance: 0,
  aop_achievement: 0,
  high_performers: 0,
  at_risk: 0,
  aop_progress: {
    total: 0,
    achieved: 0,
    by_unit: [],
  },
  talent_snapshot: {
    top_performers: [],
    at_risk: [],
  },
};

async function safeFetch<T>(path: string, defaultValue: T, params?: Record<string, unknown>): Promise<T> {
  try {
    const response = await api.get<T>(path, {
      params,
      ...( { skipErrorToast: true } as object),
    });

    if (!response.data) return defaultValue;
    return response.data;
  } catch {
    return defaultValue;
  }
}

export function useManagerDashboard() {
  const { user } = useAuth();

  const query = useQuery({
    queryKey: ["manager-dashboard", user?.id],
    enabled: Boolean(user?.id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    queryFn: async () => {
      const result = await safeFetch("/manager/dashboard", DEFAULT_MANAGER_DATA, { managerId: user?.id });

      return {
        ...DEFAULT_MANAGER_DATA,
        ...result,
        team: safeArray(result.team),
        stack_ranking: safeArray(result.stack_ranking),
        rag_heatmap: safeArray(result.rag_heatmap),
        performance_trend: safeArray(result.performance_trend),
        rating_distribution: safeArray(result.rating_distribution),
        checkin_status: safeArray(result.checkin_status),
        top_performers: safeArray(result.top_performers),
        low_performers: safeArray(result.low_performers),
        insights: safeArray((result as any).insights),
        completed_goals: safeNumber((result as any).completed_goals, 0),
      } as ManagerDashboardData;
    },
  });

  return {
    data: query.data ?? DEFAULT_MANAGER_DATA,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch(),
  };
}

export function useEmployeeDashboard() {
  const { user } = useAuth();

  const query = useQuery({
    queryKey: ["employee-dashboard", user?.id],
    enabled: Boolean(user?.id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    queryFn: async () => {
      const result = await safeFetch(
        "/employee-dashboard/overview",
        null as {
          employee_id: string;
          goals_count: number;
          avg_goal_progress: number;
          checkins_count: number;
          avg_rating: number;
          manager_name?: string | null;
          manager_email?: string | null;
          manager_title?: string | null;
        } | null,
      );

      if (!result) {
        return DEFAULT_EMPLOYEE_DATA;
      }

      return {
        ...DEFAULT_EMPLOYEE_DATA,
        overall_progress: safeNumber(result.avg_goal_progress, 0),
        goals_count: safeNumber(result.goals_count, 0),
        checkins_used: safeNumber(result.checkins_count, 0),
        avg_rating: safeNumber(result.avg_rating, 0),
        manager_name: typeof result.manager_name === "string" ? result.manager_name : null,
        manager_email: typeof result.manager_email === "string" ? result.manager_email : null,
        manager_title: typeof result.manager_title === "string" ? result.manager_title : null,
      } as EmployeeDashboardData;
    },
  });

  return {
    data: query.data ?? DEFAULT_EMPLOYEE_DATA,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch(),
  };
}

export function useHRDashboard() {
  const { user } = useAuth();

  const query = useQuery({
    queryKey: ["hr-dashboard", user?.id],
    enabled: Boolean(user?.id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    queryFn: async () => {
      const result = await safeFetch("/hr/dashboard", DEFAULT_HR_DATA);

      return {
        ...DEFAULT_HR_DATA,
        ...result,
        alerts: safeArray(result.alerts),
        training_heatmap: safeArray(result.training_heatmap),
      } as HrDashboardData;
    },
  });

  return {
    data: query.data ?? DEFAULT_HR_DATA,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch(),
  };
}

export function useLeadershipDashboard() {
  const { user } = useAuth();

  const query = useQuery({
    queryKey: ["leadership-dashboard", user?.id],
    enabled: Boolean(user?.id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    queryFn: async () => {
      const result = await safeFetch("/leadership/dashboard", DEFAULT_LEADERSHIP_DATA);

      return {
        ...DEFAULT_LEADERSHIP_DATA,
        ...result,
        aop_progress: {
          total: safeNumber((result.aop_progress as any)?.total, 0),
          achieved: safeNumber((result.aop_progress as any)?.achieved, 0),
          by_unit: safeArray((result.aop_progress as any)?.by_unit),
        },
        talent_snapshot: {
          top_performers: safeArray((result.talent_snapshot as any)?.top_performers),
          at_risk: safeArray((result.talent_snapshot as any)?.at_risk),
        },
      } as LeadershipDashboardData;
    },
  });

  return {
    data: query.data ?? DEFAULT_LEADERSHIP_DATA,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch(),
  };
}
