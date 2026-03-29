"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, Plus, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Textarea } from "@/components/ui/textarea";
import { adminService } from "@/services/admin";
import { useSessionStore } from "@/store/useSessionStore";
import type { AdminAuditLog, AdminCreateUserPayload, AdminUpdateUserPayload, AdminUser, AdminUsersListPayload, UserRole } from "@/types";

const defaultForm: AdminCreateUserPayload = {
  name: "",
  email: "",
  role: "employee",
  manager_id: null,
  department: "",
  title: "",
  password: "",
};

function parseCsvRows(csvText: string): Array<{ name: string; email: string; role: string; manager_email?: string; department?: string; title?: string }> {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length <= 1) {
    return [];
  }

  const header = lines[0].split(",").map((item) => item.trim().toLowerCase());
  const indexOf = (name: string) => header.findIndex((col) => col === name);

  const nameIdx = indexOf("name");
  const emailIdx = indexOf("email");
  const roleIdx = indexOf("role");
  const managerIdx = indexOf("manager_email");
  const departmentIdx = indexOf("department");
  const titleIdx = indexOf("title");

  if (nameIdx < 0 || emailIdx < 0 || roleIdx < 0) {
    return [];
  }

  return lines.slice(1).map((line) => {
    const cols = line.split(",").map((item) => item.trim());
    return {
      name: cols[nameIdx] || "",
      email: cols[emailIdx] || "",
      role: cols[roleIdx] || "employee",
      manager_email: managerIdx >= 0 ? cols[managerIdx] || undefined : undefined,
      department: departmentIdx >= 0 ? cols[departmentIdx] || undefined : undefined,
      title: titleIdx >= 0 ? cols[titleIdx] || undefined : undefined,
    };
  });
}

export default function AdminUsersPage() {
  const user = useSessionStore((state) => state.user);
  const [payload, setPayload] = useState<AdminUsersListPayload | null>(null);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [form, setForm] = useState<AdminCreateUserPayload>(defaultForm);
  const [bulkCsv, setBulkCsv] = useState("");
  const [filters, setFilters] = useState<{ role?: string; manager_id?: string; department?: string; status_filter?: "active" | "inactive"; search?: string }>({
    role: "",
    manager_id: "",
    department: "",
    status_filter: undefined,
    search: "",
  });

  const loadUsers = async () => {
    setLoading(true);
    try {
      const usersRes = await adminService.listUsers({
        role: filters.role || undefined,
        manager_id: filters.manager_id || undefined,
        department: filters.department || undefined,
        status_filter: filters.status_filter,
        search: filters.search || undefined,
      });
      setPayload(usersRes);
      const logs = await adminService.getAuditLogs(40);
      setAuditLogs(logs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") {
      loadUsers().catch(() => null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.role]);

  const managers = payload?.managers ?? [];
  const departments = payload?.departments ?? [];

  const roles: UserRole[] = useMemo(() => ["admin", "hr", "manager", "employee", "leadership"], []);

  const openCreateModal = () => {
    setEditing(null);
    setForm(defaultForm);
    setShowModal(true);
  };

  const openEditModal = (item: AdminUser) => {
    setEditing(item);
    setForm({
      name: item.name,
      email: item.email,
      role: item.role,
      manager_id: item.manager_id ?? null,
      department: item.department ?? "",
      title: item.title ?? "",
      password: "",
    });
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!form.name || !form.email) {
      return;
    }

    if (editing) {
      const updatePayload: AdminUpdateUserPayload = {
        name: form.name,
        email: form.email,
        role: form.role,
        manager_id: form.manager_id ?? null,
        department: form.department || null,
        title: form.title || null,
      };
      await adminService.updateUser(editing.id, updatePayload);
    } else {
      await adminService.createUser({
        ...form,
        department: form.department || null,
        title: form.title || null,
        manager_id: form.manager_id || null,
      });
    }

    setShowModal(false);
    await loadUsers();
  };

  const handleDelete = async (targetId: string) => {
    await adminService.deleteUser(targetId);
    await loadUsers();
  };

  const toggleActive = async (target: AdminUser) => {
    await adminService.updateUser(target.id, { is_active: !target.is_active });
    await loadUsers();
  };

  const handleExport = async () => {
    const rows = await adminService.exportUsers();
    if (!rows.length) {
      return;
    }

    const headers = Object.keys(rows[0]);
    const body = rows
      .map((row) => headers.map((header) => JSON.stringify(row[header] ?? "")).join(","))
      .join("\n");
    const csv = `${headers.join(",")}\n${body}`;

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "employees_export.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleBulkUpload = async () => {
    const rows = parseCsvRows(bulkCsv);
    if (!rows.length) {
      return;
    }
    await adminService.bulkUpload(rows);
    setBulkCsv("");
    await loadUsers();
  };

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Management"
        description="Full lifecycle control over users, roles, managers, activation, and data exports."
        action={
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2" onClick={handleExport}>
              <Download className="h-4 w-4" /> Export
            </Button>
            <Button className="gap-2" onClick={openCreateModal}>
              <Plus className="h-4 w-4" /> Add Employee
            </Button>
          </div>
        }
      />

      <Card className="space-y-4">
        <CardTitle>Filters</CardTitle>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <Input
            placeholder="Search name/email"
            value={filters.search || ""}
            onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
          />

          <select
            className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
            value={filters.role || ""}
            onChange={(event) => setFilters((prev) => ({ ...prev, role: event.target.value }))}
          >
            <option value="">All Roles</option>
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>

          <select
            className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
            value={filters.manager_id || ""}
            onChange={(event) => setFilters((prev) => ({ ...prev, manager_id: event.target.value }))}
          >
            <option value="">All Managers</option>
            {managers.map((manager) => (
              <option key={manager.id} value={manager.id}>
                {manager.name}
              </option>
            ))}
          </select>

          <select
            className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
            value={filters.department || ""}
            onChange={(event) => setFilters((prev) => ({ ...prev, department: event.target.value }))}
          >
            <option value="">All Departments</option>
            {departments.map((department) => (
              <option key={department} value={department}>
                {department}
              </option>
            ))}
          </select>

          <div className="flex gap-2">
            <select
              className="h-10 flex-1 rounded-lg border border-input/90 bg-card px-3 text-sm"
              value={filters.status_filter || ""}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  status_filter: (event.target.value || undefined) as "active" | "inactive" | undefined,
                }))
              }
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <Button variant="outline" onClick={() => loadUsers()} disabled={loading}>Apply</Button>
          </div>
        </div>
      </Card>

      <Card className="space-y-4">
        <CardTitle>Employees</CardTitle>
        <CardDescription>Full-width operational table with role, manager and status actions.</CardDescription>
        <DataTable
          rows={payload?.users || []}
          rowKey={(row) => row.id}
          columns={[
            { key: "name", header: "Name", render: (row) => <span className="font-medium">{row.name}</span> },
            { key: "email", header: "Email" },
            { key: "role", header: "Role", render: (row) => <Badge className="capitalize">{row.role}</Badge> },
            { key: "manager_name", header: "Manager", render: (row) => row.manager_name || "-" },
            { key: "department", header: "Department", render: (row) => row.department || "-" },
            {
              key: "is_active",
              header: "Status",
              render: (row) => (
                <Badge className={row.is_active ? "bg-emerald-500/10 text-emerald-700 ring-emerald-500/25" : "bg-amber-500/10 text-amber-700 ring-amber-500/25"}>
                  {row.is_active ? "Active" : "Inactive"}
                </Badge>
              ),
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => openEditModal(row)}>Edit</Button>
                  <Button variant="secondary" size="sm" onClick={() => toggleActive(row)}>{row.is_active ? "Deactivate" : "Activate"}</Button>
                  <Button variant="destructive" size="sm" onClick={() => handleDelete(row.id)}>Delete</Button>
                </div>
              ),
            },
          ]}
          emptyState={loading ? "Loading users..." : "No users found"}
        />
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="space-y-3">
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-4 w-4" /> Bulk Upload (CSV)
          </CardTitle>
          <CardDescription>CSV columns: name,email,role,manager_email,department,title</CardDescription>
          <Textarea
            className="min-h-40"
            value={bulkCsv}
            onChange={(event) => setBulkCsv(event.target.value)}
            placeholder="name,email,role,manager_email,department,title\nJane Doe,jane@acmepms.com,employee,manager@acmepms.com,Engineering,Software Engineer"
          />
          <div className="flex justify-end">
            <Button className="gap-2" onClick={handleBulkUpload}>
              <Upload className="h-4 w-4" /> Process CSV
            </Button>
          </div>
        </Card>

        <Card className="space-y-3">
          <CardTitle>Audit Trail</CardTitle>
          <CardDescription>Most recent admin actions for operational traceability.</CardDescription>
          <div className="max-h-56 space-y-2 overflow-auto">
            {auditLogs.map((log) => (
              <div key={log.id} className="rounded-lg border border-border/70 p-3">
                <p className="text-sm font-medium text-foreground">{log.message}</p>
                <p className="text-xs text-muted-foreground">
                  {log.action} • {new Date(log.created_at).toLocaleString()}
                </p>
              </div>
            ))}
            {auditLogs.length === 0 ? <p className="text-sm text-muted-foreground">No logs available</p> : null}
          </div>
        </Card>
      </div>

      {showModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-2xl rounded-2xl border border-border bg-card p-6 shadow-floating">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">{editing ? "Edit Employee" : "Add Employee"}</h2>
                <p className="text-sm text-muted-foreground">Manage role, manager assignment, and status.</p>
              </div>
              <Button variant="ghost" onClick={() => setShowModal(false)}>Close</Button>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Input placeholder="Name" value={form.name} onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))} />
              <Input placeholder="Email" value={form.email} onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))} />

              <select
                className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
                value={form.role}
                onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value as UserRole }))}
              >
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>

              <select
                className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
                value={form.manager_id || ""}
                onChange={(event) => setForm((prev) => ({ ...prev, manager_id: event.target.value || null }))}
              >
                <option value="">No Manager</option>
                {managers.map((manager) => (
                  <option key={manager.id} value={manager.id}>
                    {manager.name}
                  </option>
                ))}
              </select>

              <Input placeholder="Department" value={form.department || ""} onChange={(event) => setForm((prev) => ({ ...prev, department: event.target.value }))} />
              <Input placeholder="Title" value={form.title || ""} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} />

              {!editing ? (
                <Input
                  placeholder="Password (optional; auto-generated if blank)"
                  value={form.password || ""}
                  onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                />
              ) : null}
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
              <Button onClick={handleSubmit}>{editing ? "Save Changes" : "Create User"}</Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
