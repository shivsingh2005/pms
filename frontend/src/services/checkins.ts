import { api } from "@/services/api";
import type { Checkin } from "@/types";

export const checkinsService = {
  async getCheckins() {
    const { data } = await api.get<Checkin[]>("/checkins");
    return data;
  },
  async schedule(payload: {
    goal_id: string;
    employee_id: string;
    manager_id: string;
    meeting_date: string;
    meeting_link?: string;
  }) {
    const { data } = await api.post<Checkin>("/checkins", payload);
    return data;
  },
  async complete(checkinId: string, payload: { transcript?: string; summary?: string }) {
    const { data } = await api.patch<Checkin>(`/checkins/${checkinId}/complete`, payload);
    return data;
  },
};
