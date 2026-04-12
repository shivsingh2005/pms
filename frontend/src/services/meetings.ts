import { api } from "@/services/api";
import type { Meeting } from "@/types";

interface MeetingPayload {
  title: string;
  meeting_type?: "CHECKIN" | "GENERAL" | "HR" | "REVIEW";
  description?: string;
  start_time: string;
  end_time: string;
  participants: string[];
  checkin_id?: string;
  goal_id?: string;
  goal_ids?: string[];
}

export const meetingsService = {
  async getMeetings() {
    const { data } = await api.get<Meeting[]>("/meetings");
    return data;
  },
  async createMeeting(payload: MeetingPayload) {
    const { data } = await api.post<Meeting>("/meetings/create", payload);
    return data;
  },
  async updateMeeting(id: string, payload: Partial<MeetingPayload>) {
    const { data } = await api.patch<Meeting>(`/meetings/${id}`, payload);
    return data;
  },
  async cancelMeeting(id: string) {
    const { data } = await api.delete<Meeting>(`/meetings/${id}`);
    return data;
  },
  async summarizeMeeting(id: string) {
    const { data } = await api.post<{ meeting_id: string; summary: string; key_points: string[]; action_items: string[] }>(
      `/meetings/${id}/ai-summary`,
    );
    return data;
  },
};
