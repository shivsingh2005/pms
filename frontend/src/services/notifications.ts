import { api } from "@/services/api";
import type { NotificationsPayload } from "@/types";

export const notificationsService = {
  async list(unread = false) {
    const { data } = await api.get<NotificationsPayload>("/notifications", {
      params: { unread },
      ...( { skipErrorToast: true } as object),
    });
    return data;
  },

  async markRead(notificationId: string) {
    await api.post(`/notifications/mark-read/${notificationId}`);
  },

  async markAllRead() {
    await api.post("/notifications/mark-all-read");
  },
};
