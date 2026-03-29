import { api } from "@/services/api";
import type { Checkin, CheckinRating } from "@/types";

export const checkinsService = {
  async getCheckins() {
    const { data } = await api.get<Checkin[]>("/checkins");
    return data;
  },
  async submit(payload: {
    goal_id: string;
    progress: number;
    summary: string;
    blockers?: string;
    next_steps?: string;
  }) {
    const { data } = await api.post<{ checkin: Checkin; insights: string[] }>("/checkins", payload);
    return data;
  },
  async review(checkinId: string, payload: { manager_feedback: string; status?: "reviewed" }) {
    const { data } = await api.patch<Checkin>(`/checkins/${checkinId}`, {
      ...payload,
      status: payload.status ?? "reviewed",
    });
    return data;
  },
  async rate(checkinId: string, payload: { rating: number; feedback?: string }) {
    const { data } = await api.post<CheckinRating>(`/checkins/${checkinId}/rate`, payload);
    return data;
  },
  async getFinalRating(employeeId: string) {
    const { data } = await api.get<{ employee_id: string; average_rating: number; ratings_count: number }>(
      `/checkins/employee/${employeeId}/final-rating`,
    );
    return data;
  },
};
