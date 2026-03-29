"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { adminService } from "@/services/admin";
import { useSessionStore } from "@/store/useSessionStore";
import type { AdminOrgManagerNode, AdminOrgStructurePayload, AdminUser } from "@/types";

export default function AdminOrganizationPage() {
  const user = useSessionStore((state) => state.user);
  const [payload, setPayload] = useState<AdminOrgStructurePayload | null>(null);
  const [selectedManager, setSelectedManager] = useState<AdminOrgManagerNode | null>(null);
  const [selectedMember, setSelectedMember] = useState<AdminUser | null>(null);
  const [newManagerId, setNewManagerId] = useState("");

  const load = async () => {
    const data = await adminService.getOrgStructure();
    setPayload(data);
    if (data.managers.length > 0 && !selectedManager) {
      setSelectedManager(data.managers[0]);
    }
  };

  useEffect(() => {
    if (user) {
      load().catch(() => null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleReassign = async () => {
    if (!selectedMember || !newManagerId) {
      return;
    }
    await adminService.updateUser(selectedMember.id, { manager_id: newManagerId });
    setSelectedMember(null);
    setNewManagerId("");
    await load();
  };

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organization Structure"
        description="Leadership to manager to employee hierarchy with team-level visibility and reassignment controls."
      />

      <Card className="space-y-3">
        <CardTitle>Leadership</CardTitle>
        <CardDescription>Top-level leadership and admin users for this organization.</CardDescription>
        <div className="flex flex-wrap gap-2">
          {(payload?.leaders || []).map((leader) => (
            <Badge key={leader.id} className="bg-sky-500/10 text-sky-700 ring-sky-500/25">
              {leader.name} ({leader.role})
            </Badge>
          ))}
          {!payload?.leaders?.length ? <p className="text-sm text-muted-foreground">No leadership users found.</p> : null}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="space-y-3 xl:col-span-1">
          <CardTitle>Managers</CardTitle>
          <CardDescription>Team size and average team rating.</CardDescription>
          <div className="space-y-2">
            {(payload?.managers || []).map((manager) => (
              <button
                key={manager.manager_id}
                type="button"
                onClick={() => setSelectedManager(manager)}
                className={`w-full rounded-lg border p-3 text-left transition ${selectedManager?.manager_id === manager.manager_id ? "border-primary/40 bg-primary/5" : "border-border/70 bg-card"}`}
              >
                <p className="text-sm font-medium text-foreground">{manager.manager_name}</p>
                <p className="text-xs text-muted-foreground">
                  Team: {manager.team_size} • Avg Rating: {manager.avg_team_rating.toFixed(2)}
                </p>
              </button>
            ))}
          </div>
        </Card>

        <Card className="space-y-3 xl:col-span-2">
          <CardTitle>{selectedManager ? `${selectedManager.manager_name}'s Team` : "Team Members"}</CardTitle>
          <CardDescription>Click a member to reassign them to a different manager.</CardDescription>
          <div className="space-y-2">
            {(selectedManager?.members || []).map((member) => (
              <button
                key={member.id}
                type="button"
                className={`w-full rounded-lg border p-3 text-left transition ${selectedMember?.id === member.id ? "border-primary/40 bg-primary/5" : "border-border/70 bg-card"}`}
                onClick={() => {
                  setSelectedMember(member);
                  setNewManagerId(member.manager_id || "");
                }}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{member.name}</p>
                  <Badge className={member.is_active ? "bg-emerald-500/10 text-emerald-700 ring-emerald-500/25" : "bg-amber-500/10 text-amber-700 ring-amber-500/25"}>
                    {member.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {member.role} • {member.department || "No department"} • {member.email}
                </p>
              </button>
            ))}
            {!selectedManager?.members?.length ? <p className="text-sm text-muted-foreground">No team members for this manager.</p> : null}
          </div>

          {selectedMember ? (
            <div className="rounded-xl border border-border/70 bg-surface/70 p-4">
              <p className="text-sm font-medium text-foreground">Reassign {selectedMember.name}</p>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                <select
                  className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
                  value={newManagerId}
                  onChange={(event) => setNewManagerId(event.target.value)}
                >
                  <option value="">No Manager</option>
                  {(payload?.managers || []).map((manager) => (
                    <option key={manager.manager_id} value={manager.manager_id}>
                      {manager.manager_name}
                    </option>
                  ))}
                </select>
                <Input value={selectedMember.email} disabled />
              </div>
              <div className="mt-3 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setSelectedMember(null)}>Cancel</Button>
                <Button onClick={handleReassign}>Reassign</Button>
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
