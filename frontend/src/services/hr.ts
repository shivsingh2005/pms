import { api } from "@/services/api";
import type {
  HRCalibrationPayload,
  HREmployeeDirectoryItem,
  HREmployeePerformance,
  HREmployeeProfile,
  HRManagerOption,
  HRManagerTeamSummary,
  HRMeeting,
  HROrgAnalytics,
  HROverview,
  HRReportPayload,
  HRTeamInsights,
} from "@/types";

interface TeamFilterParams {
  department?: string;
  role?: string;
  performance?: "on_track" | "needs_attention" | "at_risk";
}

interface HRMeetingCreatePayload {
  title: string;
  meeting_type?: "CHECKIN" | "GENERAL" | "HR" | "REVIEW";
  description?: string;
  start_time: string;
  end_time: string;
  participants: string[];
  goal_id?: string;
  employee_id?: string;
  manager_id?: string;
}

interface HRMeetingUpdatePayload {
  title?: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  participants?: string[];
}

export const hrService = {
  async getOverview() {
    const { data } = await api.get<HROverview>("/hr/overview");
    return data;
  },

  async getManagers(department?: string) {
    const { data } = await api.get<HRManagerOption[]>("/hr/managers", {
      params: { department: department || undefined },
    });
    return data;
  },

  async getTeamByManager(managerId: string, filters?: TeamFilterParams) {
    const { data } = await api.get<HREmployeePerformance[]>(`/hr/team/${managerId}`, {
      params: {
        department: filters?.department || undefined,
        role: filters?.role || undefined,
        performance: filters?.performance || undefined,
      },
    });
    return data;
  },

  async getTeamInsights(managerId: string, filters?: TeamFilterParams) {
    const { data } = await api.get<HRTeamInsights>(`/hr/team/${managerId}/insights`, {
      params: {
        department: filters?.department || undefined,
        role: filters?.role || undefined,
        performance: filters?.performance || undefined,
      },
    });
    return data;
  },

  async getEmployees(params?: { department?: string; manager_id?: string; needs_training?: boolean }) {
    const { data } = await api.get<HREmployeeDirectoryItem[]>("/hr/employees", { params });
    return data;
  },

  async getEmployeeProfile(employeeId: string) {
    const { data } = await api.get<HREmployeeProfile>(`/hr/employees/${employeeId}`);
    return data;
  },

  async getManagerTeamAnalytics(managerId: string) {
    const { data } = await api.get<HRManagerTeamSummary>(`/hr/manager-team/${managerId}`);
    return data;
  },

  async getOrgAnalytics() {
    const { data } = await api.get<HROrgAnalytics>("/hr/analytics");
    return data;
  },

  async getCalibration() {
    const { data } = await api.get<HRCalibrationPayload>("/hr/calibration");
    return data;
  },

  async getReport(reportType: "employee" | "team" | "org") {
    const { data } = await api.get<HRReportPayload>("/hr/reports", { params: { report_type: reportType } });
    return data;
  },

  async getMeetings(params?: { employee_id?: string; manager_id?: string }) {
    const { data } = await api.get<HRMeeting[]>("/hr/meetings", { params });
    return data;
  },

  async createMeeting(payload: HRMeetingCreatePayload) {
    const { data } = await api.post<HRMeeting>("/meetings/create", payload);
    return data;
  },

  async updateMeeting(meetingId: string, payload: HRMeetingUpdatePayload) {
    const { data } = await api.patch<HRMeeting>(`/meetings/${meetingId}`, payload);
    return data;
  },

  async cancelMeeting(meetingId: string) {
    const { data } = await api.delete<HRMeeting>(`/meetings/${meetingId}`);
    return data;
  },

  async summarizeMeeting(meetingId: string, transcript: string) {
    const { data } = await api.post<{ meeting_id: string; summary: string }>(`/hr/meetings/${meetingId}/summarize`, { transcript });
    return data;
  },
};
