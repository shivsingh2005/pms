import { api } from "@/services/api";
import type {
  ManagerEmployeeInspection,
  ManagerPendingCheckin,
  ManagerStackRankingPayload,
  ManagerTeamMember,
  ManagerTeamPerformancePayload,
  Meeting,
  MeetingProposal,
} from "@/types";

export const managerService = {
  async getDashboard(managerId: string, options?: { silent?: boolean }) {
    const { data } = await api.get<ManagerTeamPerformancePayload>("/manager/dashboard", {
      params: { managerId },
      ...(options?.silent ? ({ skipErrorToast: true } as object) : {}),
    });
    return data;
  },
  async getTeam(options?: { silent?: boolean }) {
    const { data } = await api.get<ManagerTeamMember[]>("/manager/team", options?.silent ? ({ skipErrorToast: true } as object) : undefined);
    return data;
  },
  async inspectEmployee(employeeId: string) {
    const { data } = await api.get<ManagerEmployeeInspection>(`/manager/employee/${employeeId}`);
    return data;
  },
  async getTeamPerformance(options?: { silent?: boolean }) {
    const { data } = await api.get<ManagerTeamPerformancePayload>("/manager/team-performance", options?.silent ? ({ skipErrorToast: true } as object) : undefined);
    return data;
  },
  async getStackRanking(payload?: {
    sort_by?: "progress" | "rating" | "consistency";
    order?: "asc" | "desc";
    at_risk_only?: boolean;
    limit?: number;
  }) {
    const { data } = await api.get<ManagerStackRankingPayload>("/manager/stack-ranking", { params: payload });
    return data;
  },
  async getPendingCheckins(options?: { silent?: boolean }) {
    const { data } = await api.get<ManagerPendingCheckin[]>("/manager/checkins", options?.silent ? ({ skipErrorToast: true } as object) : undefined);
    return data;
  },
  async getPendingMeetingProposals(options?: { silent?: boolean }) {
    const { data } = await api.get<MeetingProposal[]>("/meetings/proposals/pending", options?.silent ? ({ skipErrorToast: true } as object) : undefined);
    return data;
  },
  async approveMeetingProposal(proposalId: string) {
    const { data } = await api.post<Meeting>(`/meetings/proposal/${proposalId}/approve`);
    return data;
  },
  async rejectMeetingProposal(proposalId: string, suggest_new_start_time?: string) {
    const { data } = await api.post<MeetingProposal>(`/meetings/proposal/${proposalId}/reject`, {
      suggest_new_start_time: suggest_new_start_time ?? null,
    });
    return data;
  },
  async rescheduleMeetingProposal(proposalId: string, payload: { proposed_start_time: string; proposed_end_time: string }) {
    const { data } = await api.patch<MeetingProposal>(`/meetings/proposal/${proposalId}/reschedule`, payload);
    return data;
  },
};
