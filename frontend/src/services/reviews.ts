import { api } from "@/services/api";
import type { Review, ReviewNarrative, ReviewNarrativeRequest } from "@/types";

export const reviewsService = {
  async getReviews() {
    const { data } = await api.get<Review[]>("/reviews");
    return data;
  },
  async getNarrative(payload: ReviewNarrativeRequest) {
    const { data } = await api.post<ReviewNarrative>("/reviews/narrative", payload);
    return data;
  },
};
