"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useSessionStore } from "@/store/useSessionStore";
import { managerService } from "@/services/manager";
import { fixed, n } from "@/lib/safe";
import type { ManagerTeamMember } from "@/types";

type SortKey = "performance" | "name";

function initials(name: string): string {
  const parts = name.trim().split(" ").filter(Boolean);
  if (parts.length === 0) return "NA";
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export default function ManagerTeamDashboardPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);

  const [loading, setLoading] = useState(false);
  const [members, setMembers] = useState<ManagerTeamMember[]>([]);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("performance");

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, router, setActiveMode, user]);

  useEffect(() => {
    if (!user || activeMode !== "manager") return;
    setLoading(true);
    managerService
      .getTeam()
      .then(setMembers)
      .catch(() => toast.error("Failed to load team members"))
      .finally(() => setLoading(false));
  }, [activeMode, user]);

  const roleOptions = useMemo(() => {
    const unique = Array.from(new Set(members.map((item) => item.role))).sort();
    return ["all", ...unique];
  }, [members]);

  const filteredMembers = useMemo(() => {
    const query = search.trim().toLowerCase();
    const next = members.filter((member) => {
      const matchesQuery =
        query.length === 0 ||
        member.name.toLowerCase().includes(query) ||
        member.department.toLowerCase().includes(query) ||
        member.role.toLowerCase().includes(query);
      const matchesRole = roleFilter === "all" || member.role === roleFilter;
      return matchesQuery && matchesRole;
    });

    next.sort((a, b) => {
      if (sortKey === "name") {
        return a.name.localeCompare(b.name);
      }
      return b.goal_progress_percent - a.goal_progress_percent;
    });

    return next;
  }, [members, roleFilter, search, sortKey]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Team Dashboard"
        description="View your direct reports, monitor performance, and open complete employee profiles."
        action={<Button variant="outline" onClick={() => router.refresh()}>Refresh View</Button>}
      />

      <Card className="rounded-xl border bg-card p-5 space-y-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by name, role, or department"
          />
          <select
            className="h-10 w-full rounded-lg border border-input/90 bg-card px-3 text-sm text-foreground outline-none"
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value)}
          >
            {roleOptions.map((role) => (
              <option key={role} value={role}>
                {role === "all" ? "All Roles" : role}
              </option>
            ))}
          </select>
          <select
            className="h-10 w-full rounded-lg border border-input/90 bg-card px-3 text-sm text-foreground outline-none"
            value={sortKey}
            onChange={(event) => setSortKey(event.target.value as SortKey)}
          >
            <option value="performance">Sort by Performance</option>
            <option value="name">Sort by Name</option>
          </select>
        </div>
      </Card>

      {loading && <Card className="rounded-xl border bg-card p-5"><CardDescription>Loading team members...</CardDescription></Card>}

      {!loading && (
        <Card className="rounded-xl border bg-card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Employee</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Department</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Goal Progress</th>
                  <th className="px-4 py-3 font-medium">Final Rating</th>
                  <th className="px-4 py-3 font-medium">Consistency</th>
                  <th className="px-4 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredMembers.map((member) => {
                  const profileId = member.id || (member as { employee_id?: string }).employee_id || "";
                  return (
                    <tr key={member.id} className="border-t border-border/60 align-middle hover:bg-muted/20">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          {member.profile_avatar ? (
                            <Image
                              src={member.profile_avatar}
                              alt={member.name}
                              width={36}
                              height={36}
                              className="h-9 w-9 rounded-full border border-border/70 object-cover"
                            />
                          ) : (
                            <div className="grid h-9 w-9 place-items-center rounded-full border border-border/70 bg-muted/60 text-xs font-semibold text-muted-foreground">
                              {initials(member.name)}
                            </div>
                          )}
                          <div>
                            <p className="font-medium text-foreground">{member.name}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{member.role}</td>
                      <td className="px-4 py-3 text-muted-foreground">{member.department}</td>
                      <td className="px-4 py-3">
                        <Badge className={member.status === "On Track" ? "bg-success/15 text-success ring-success/25" : "bg-error/15 text-error ring-error/25"}>
                          {member.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-1.5">
                          <p className="text-xs text-muted-foreground">{member.goal_progress_percent}%</p>
                          <Progress value={member.goal_progress_percent} className="h-2" />
                        </div>
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground">{fixed(n(member.avg_final_rating, 0), 2)}</td>
                      <td className="px-4 py-3 font-medium text-foreground">{fixed(n(member.consistency_percent, 0), 1)}%</td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!profileId}
                          onClick={() => {
                            if (!profileId) return;
                            router.push(`/manager/employee/${profileId}`);
                          }}
                        >
                          Open Profile
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {!loading && filteredMembers.length === 0 && (
        <Card className="rounded-xl border bg-card p-5">
          <CardDescription>No team members matched your filters.</CardDescription>
        </Card>
      )}
    </motion.div>
  );
}

