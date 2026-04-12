import { api } from "@/services/api";
import type { NotificationItem } from "@/types";
import type { NotificationsPayload } from "@/types";

type LegacyNotificationsResponse = {
  notifications?: Array<{
    id?: string;
    user_id?: string;
    title?: string;
    message?: string;
    type?: string;
    notification_type?: string;
    action_url?: string | null;
    is_read?: boolean;
    created_at?: string;
  }>;
  total?: number;
};

function normalizeNotificationsPayload(value: unknown): NotificationsPayload {
  if (!value || typeof value !== "object") {
    return { unread_count: 0, items: [] };
  }

  const payload = value as Partial<NotificationsPayload> & LegacyNotificationsResponse;
  const rawItems = Array.isArray(payload.items)
    ? payload.items
    : Array.isArray(payload.notifications)
      ? payload.notifications
      : [];

  const items: NotificationItem[] = rawItems.map((row) => {
    const legacyRow = row as NonNullable<LegacyNotificationsResponse["notifications"]>[number] | undefined;
    return {
      id: String(row.id ?? ""),
      user_id: String(row.user_id ?? ""),
      type: String(row.type ?? legacyRow?.notification_type ?? "SYSTEM"),
      title: String(row.title ?? "Notification"),
      message: String(row.message ?? ""),
      action_url: row.action_url ?? null,
      is_read: Boolean(row.is_read),
      created_at: String(row.created_at ?? new Date().toISOString()),
    };
  });

  const unreadCount = typeof payload.unread_count === "number"
    ? payload.unread_count
    : items.reduce((count, item) => count + (item.is_read ? 0 : 1), 0);

  return {
    unread_count: unreadCount,
    items,
  };
}

export const notificationsService = {
  async list(unread = false) {
    const { data } = await api.get<NotificationsPayload | LegacyNotificationsResponse>("/notifications", {
      params: { unread },
      ...( { skipErrorToast: true } as object),
    });
    return normalizeNotificationsPayload(data);
  },

  async markRead(notificationId: string) {
    await api.post(`/notifications/mark-read/${notificationId}`);
  },

  async markAllRead() {
    await api.post("/notifications/mark-all-read");
  },
};
