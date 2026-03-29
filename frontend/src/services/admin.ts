import { api } from "@/services/api";
import type {
  AdminAuditLog,
  AdminBulkUploadResult,
  AdminCreateUserPayload,
  AdminDashboardPayload,
  AdminOrgStructurePayload,
  AdminRolePermission,
  AdminSystemSettings,
  AdminUpdateUserPayload,
  AdminUpsertRolePayload,
  AdminUser,
  AdminUsersListPayload,
} from "@/types";

interface UserFilters {
  role?: string;
  manager_id?: string;
  department?: string;
  status_filter?: "active" | "inactive";
  search?: string;
}

export const adminService = {
  async getDashboard() {
    const { data } = await api.get<AdminDashboardPayload>("/admin/dashboard");
    return data;
  },

  async listUsers(filters?: UserFilters) {
    const { data } = await api.get<AdminUsersListPayload>("/admin/users", { params: filters });
    return data;
  },

  async createUser(payload: AdminCreateUserPayload) {
    const { data } = await api.post<AdminUser>("/admin/users", payload);
    return data;
  },

  async updateUser(userId: string, payload: AdminUpdateUserPayload) {
    const { data } = await api.put<AdminUser>(`/admin/users/${userId}`, payload);
    return data;
  },

  async deleteUser(userId: string) {
    await api.delete(`/admin/users/${userId}`);
  },

  async bulkUpload(users: Array<{ name: string; email: string; role: string; manager_email?: string; department?: string; title?: string }>) {
    const { data } = await api.post<AdminBulkUploadResult>("/admin/users/bulk-upload", { users });
    return data;
  },

  async exportUsers() {
    const { data } = await api.get<Array<Record<string, unknown>>>("/admin/users/export");
    return data;
  },

  async getRoles() {
    const { data } = await api.get<AdminRolePermission[]>("/admin/roles");
    return data;
  },

  async upsertRole(payload: AdminUpsertRolePayload) {
    const { data } = await api.post<AdminRolePermission>("/admin/roles", payload);
    return data;
  },

  async updateRoles(roles: AdminUpsertRolePayload[]) {
    const { data } = await api.put<AdminRolePermission[]>("/admin/roles", { roles });
    return data;
  },

  async deleteRole(roleKey: string) {
    await api.delete(`/admin/roles/${roleKey}`);
  },

  async getOrgStructure() {
    const { data } = await api.get<AdminOrgStructurePayload>("/admin/org-structure");
    return data;
  },

  async getSettings() {
    const { data } = await api.get<AdminSystemSettings>("/admin/settings");
    return data;
  },

  async updateSettings(payload: Partial<AdminSystemSettings> & { ai_settings?: Record<string, unknown> & { api_key?: string } }) {
    const { data } = await api.put<AdminSystemSettings>("/admin/settings", payload);
    return data;
  },

  async getAuditLogs(limit = 100) {
    const { data } = await api.get<AdminAuditLog[]>("/admin/audit-logs", { params: { limit } });
    return data;
  },

  async getRoleHistory(limit = 100) {
    const { data } = await api.get<AdminAuditLog[]>("/admin/role-history", { params: { limit } });
    return data;
  },
};
