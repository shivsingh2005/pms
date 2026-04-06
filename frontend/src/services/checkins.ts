import { api } from "@/services/api";
import type {
  Checkin,
  CheckinRating,
  CheckinRatingRecommendation,
  CheckinTranscriptIngestResult,
} from "@/types";

export const checkinsService = {
  async getCheckins() {
    const { data } = await api.get<Checkin[]>("/checkins");
    return data;
  },
  async submit(payload: {
    overall_progress: number;
    summary: string;
    achievements?: string;
    blockers?: string;
    confidence_level?: number;
    is_final?: boolean;
    goal_updates?: Array<{ goal_id: string; progress?: number; note?: string }>;
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
  async getFinalRatingsBulk(employeeIds: string[]) {
    const uniqueEmployeeIds = Array.from(new Set(employeeIds.filter(Boolean)));
    if (!uniqueEmployeeIds.length) {
      return [] as Array<{ employee_id: string; average_rating: number; ratings_count: number }>;
    }

    const { data } = await api.post<{
      items: Array<{ employee_id: string; average_rating: number; ratings_count: number }>;
    }>("/checkins/employee/final-ratings", {
      employee_ids: uniqueEmployeeIds,
    });
    return data.items;
  },
  async ingestTranscript(checkinId: string, transcript: string) {
    const { data } = await api.post<CheckinTranscriptIngestResult>(`/checkins/${checkinId}/transcript/ingest`, {
      transcript,
    });
    return data;
  },
  async getRatingRecommendation(checkinId: string) {
    const { data } = await api.get<CheckinRatingRecommendation>(`/checkins/${checkinId}/rating-recommendation`);
    return data;
  },
};
