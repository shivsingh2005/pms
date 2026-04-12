import { api } from "@/services/api";
import type {
  AnnualOperatingPlanItem,
  DepartmentFrameworkPolicy,
  PerformanceCyclesListResponse,
  FrameworkRecommendation,
  FrameworkSelection,
  KPILibraryItem,
} from "@/types";

export const performanceCyclesService = {
  async listCycles() {
    const { data } = await api.get<PerformanceCyclesListResponse>("/performance-cycles");
    return data;
  },

  async recommendFramework(payload: { role: string; department?: string }) {
    const { data } = await api.get<FrameworkRecommendation>("/performance-cycles/framework/recommend", {
      params: {
        role: payload.role,
        department: payload.department || undefined,
      },
    });
    return data;
  },

  async getFrameworkSelection() {
    const { data } = await api.get<FrameworkSelection | null>("/performance-cycles/framework/selection");
    return data;
  },

  async saveFrameworkSelection(payload: { selected_framework: string; cycle_type?: string }) {
    const { data } = await api.post<FrameworkSelection>("/performance-cycles/framework/selection", {
      selected_framework: payload.selected_framework,
      cycle_type: payload.cycle_type || "quarterly",
    });
    return data;
  },

  async listFrameworkPolicies() {
    const { data } = await api.get<DepartmentFrameworkPolicy[]>("/performance-cycles/framework/policies");
    return data;
  },

  async upsertFrameworkPolicy(payload: {
    department: string;
    allowed_frameworks: string[];
    cycle_type?: string;
    is_active?: boolean;
  }) {
    const { data } = await api.post<DepartmentFrameworkPolicy>("/performance-cycles/framework/policies", {
      department: payload.department,
      allowed_frameworks: payload.allowed_frameworks,
      cycle_type: payload.cycle_type || "quarterly",
      is_active: payload.is_active ?? true,
    });
    return data;
  },

  async listKpiLibrary(filters?: { role?: string; department?: string; framework?: string }) {
    const { data } = await api.get<KPILibraryItem[]>("/performance-cycles/kpi-library", {
      params: {
        role: filters?.role || undefined,
        department: filters?.department || undefined,
        framework: filters?.framework || undefined,
      },
    });
    return data;
  },

  async createKpiLibraryItem(payload: {
    role: string;
    domain?: string;
    department?: string;
    goal_title: string;
    goal_description: string;
    suggested_kpi: string;
    suggested_weight: number;
    framework: string;
  }) {
    const { data } = await api.post<KPILibraryItem>("/performance-cycles/kpi-library", payload);
    return data;
  },

  async listAop(filters?: { year?: number; department?: string }) {
    const { data } = await api.get<AnnualOperatingPlanItem[]>("/performance-cycles/aop", {
      params: {
        year: filters?.year || undefined,
        department: filters?.department || undefined,
      },
    });
    return data;
  },

  async createAop(payload: { year: number; objective: string; target_value?: string; department?: string }) {
    const { data } = await api.post<AnnualOperatingPlanItem>("/performance-cycles/aop", payload);
    return data;
  },
};
