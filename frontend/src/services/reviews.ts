import { api } from "@/services/api";
import type { Review } from "@/types";

export const reviewsService = {
  async getReviews() {
    const { data } = await api.get<Review[]>("/reviews");
    return data;
  },
};
