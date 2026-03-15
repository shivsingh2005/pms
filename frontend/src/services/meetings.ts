import { api } from "@/services/api";
import type { Meeting } from "@/types";

interface MeetingPayload {
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  participants: string[];
  goal_id: string;
}

export const meetingsService = {
  async getMeetings(googleAccessToken: string) {
    const { data } = await api.get<Meeting[]>("/meetings", {
      headers: { "X-Google-Access-Token": googleAccessToken },
    });
    return data;
  },
  async createMeeting(payload: MeetingPayload, googleAccessToken: string) {
    const { data } = await api.post<Meeting>("/meetings/create", payload, {
      headers: { "X-Google-Access-Token": googleAccessToken },
    });
    return data;
  },
  async updateMeeting(id: string, payload: Partial<MeetingPayload>, googleAccessToken: string) {
    const { data } = await api.patch<Meeting>(`/meetings/${id}`, payload, {
      headers: { "X-Google-Access-Token": googleAccessToken },
    });
    return data;
  },
  async cancelMeeting(id: string, googleAccessToken: string) {
    const { data } = await api.delete<Meeting>(`/meetings/${id}`, {
      headers: { "X-Google-Access-Token": googleAccessToken },
    });
    return data;
  },
};
