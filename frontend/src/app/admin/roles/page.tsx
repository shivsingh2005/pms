"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Textarea } from "@/components/ui/textarea";
import { adminService } from "@/services/admin";
import { useSessionStore } from "@/store/useSessionStore";
import type { AdminAuditLog, AdminRolePermission } from "@/types";

export default function AdminRolesPage() {
  const user = useSessionStore((state) => state.user);
  const [roles, setRoles] = useState<AdminRolePermission[]>([]);
  const [roleHistory, setRoleHistory] = useState<AdminAuditLog[]>([]);
  const [editingRole, setEditingRole] = useState<AdminRolePermission | null>(null);
  const [roleKey, setRoleKey] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [permissionsText, setPermissionsText] = useState("");

  const load = async () => {
    const [rolesData, historyData] = await Promise.all([adminService.getRoles(), adminService.getRoleHistory(80)]);
    setRoles(rolesData);
    setRoleHistory(historyData);
  };

  useEffect(() => {
    if (user) {
      load().catch(() => null);
    }
  }, [user]);

  const parsedPermissions = useMemo(
    () => permissionsText.split(",").map((item) => item.trim()).filter(Boolean),
    [permissionsText],
  );

  const startCreate = () => {
    setEditingRole(null);
    setRoleKey("");
    setDisplayName("");
    setPermissionsText("");
  };

  const startEdit = (role: AdminRolePermission) => {
    setEditingRole(role);
    setRoleKey(role.role_key);
    setDisplayName(role.display_name);
    setPermissionsText(role.permissions.join(", "));
  };

  const saveRole = async () => {
    if (!roleKey.trim() || !displayName.trim() || parsedPermissions.length === 0) {
      return;
    }
    await adminService.upsertRole({
      role_key: roleKey.trim().toLowerCase(),
      display_name: displayName.trim(),
      permissions: parsedPermissions,
    });
    await load();
    startCreate();
  };

  const deleteRole = async (role: AdminRolePermission) => {
    await adminService.deleteRole(role.role_key);
    await load();
    if (editingRole?.role_key === role.role_key) {
      startCreate();
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Role Management"
        description="Manage role catalog and access permissions for system features."
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="space-y-4 xl:col-span-2">
          <CardTitle>Roles & Permissions</CardTitle>
          <CardDescription>System roles are protected. Custom roles can be created, edited, and removed.</CardDescription>
          <DataTable
            rows={roles}
            rowKey={(row) => row.role_key}
            columns={[
              { key: "role_key", header: "Role Key", render: (row) => <span className="font-medium">{row.role_key}</span> },
              { key: "display_name", header: "Display Name" },
              {
                key: "permissions",
                header: "Permissions",
                render: (row) => (
                  <div className="flex flex-wrap gap-1">
                    {row.permissions.map((permission) => (
                      <Badge key={permission} className="bg-primary/5 text-primary ring-primary/10">
                        {permission}
                      </Badge>
                    ))}
                  </div>
                ),
              },
              {
                key: "is_system",
                header: "Type",
                render: (row) => (
                  <Badge className={row.is_system ? "bg-sky-500/10 text-sky-700 ring-sky-500/25" : "bg-emerald-500/10 text-emerald-700 ring-emerald-500/25"}>
                    {row.is_system ? "System" : "Custom"}
                  </Badge>
                ),
              },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => startEdit(row)}>Edit</Button>
                    {!row.is_system ? (
                      <Button variant="destructive" size="sm" onClick={() => deleteRole(row)}>Delete</Button>
                    ) : null}
                  </div>
                ),
              },
            ]}
          />
        </Card>

        <Card className="space-y-3">
          <CardTitle>{editingRole ? `Edit Role: ${editingRole.role_key}` : "Create Role"}</CardTitle>
          <CardDescription>Use comma-separated permission keys, like users:create, checkins:approve.</CardDescription>

          <Input
            placeholder="Role key (example: contractor_manager)"
            value={roleKey}
            disabled={Boolean(editingRole?.is_system)}
            onChange={(event) => setRoleKey(event.target.value)}
          />
          <Input
            placeholder="Display name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
          />
          <Textarea
            className="min-h-32"
            placeholder="users:view, users:update, reports:view"
            value={permissionsText}
            onChange={(event) => setPermissionsText(event.target.value)}
          />

          <div className="flex gap-2">
            <Button onClick={saveRole}>Save Role</Button>
            <Button variant="outline" onClick={startCreate}>Reset</Button>
          </div>
        </Card>
      </div>

      <Card className="space-y-3">
        <CardTitle>Role Change History</CardTitle>
        <CardDescription>Audit trail for role creation, updates, deletion, and user role changes.</CardDescription>
        <div className="max-h-64 space-y-2 overflow-auto">
          {roleHistory.map((entry) => (
            <div key={entry.id} className="rounded-lg border border-border/70 p-3">
              <p className="text-sm font-medium text-foreground">{entry.message}</p>
              <p className="text-xs text-muted-foreground">
                {entry.action} • {new Date(entry.created_at).toLocaleString()}
              </p>
            </div>
          ))}
          {roleHistory.length === 0 ? <p className="text-sm text-muted-foreground">No role history available.</p> : null}
        </div>
      </Card>
    </div>
  );
}
