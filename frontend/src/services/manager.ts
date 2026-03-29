import { api } from "@/services/api";
import type {
  ManagerEmployeeInspection,
  ManagerPendingCheckin,
  ManagerTeamMember,
  ManagerTeamPerformancePayload,
  Meeting,
  MeetingProposal,
} from "@/types";

export const managerService = {
  async getTeam() {
    const { data } = await api.get<ManagerTeamMember[]>("/manager/team");
    return data;
  },
  async inspectEmployee(employeeId: string) {
    const { data } = await api.get<ManagerEmployeeInspection>(`/manager/employee/${employeeId}`);
    return data;
  },
  async getTeamPerformance() {
    const { data } = await api.get<ManagerTeamPerformancePayload>("/manager/team-performance");
    return data;
  },
  async getPendingCheckins() {
    const { data } = await api.get<ManagerPendingCheckin[]>("/manager/checkins");
    return data;
  },
  async getPendingMeetingProposals() {
    const { data } = await api.get<MeetingProposal[]>("/meetings/proposals/pending");
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
