"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useSessionStore } from "@/store/useSessionStore";
import { managerService } from "@/services/manager";
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
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMembers.map((member) => (
            <button
              key={member.id}
              className="text-left"
              onClick={() => router.push(`/manager/employee/${member.id}`)}
              type="button"
            >
              <Card className="rounded-xl border bg-card p-5 space-y-4 hover:border-primary/40 hover:shadow-soft">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    {member.profile_avatar ? (
                      <Image
                        src={member.profile_avatar}
                        alt={member.name}
                        width={44}
                        height={44}
                        className="h-11 w-11 rounded-full object-cover border border-border/70"
                      />
                    ) : (
                      <div className="h-11 w-11 rounded-full border border-border/70 bg-muted/60 grid place-items-center text-sm font-semibold text-muted-foreground">
                        {initials(member.name)}
                      </div>
                    )}
                    <div>
                      <CardTitle className="text-base">{member.name}</CardTitle>
                      <CardDescription>{member.role}</CardDescription>
                      <CardDescription>{member.department}</CardDescription>
                    </div>
                  </div>
                  <Badge className={member.status === "On Track" ? "bg-success/15 text-success ring-success/25" : "bg-error/15 text-error ring-error/25"}>
                    {member.status}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Goal Progress</span>
                    <span className="font-semibold">{member.goal_progress_percent}%</span>
                  </div>
                  <Progress value={member.goal_progress_percent} />
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
                  <div className="rounded-md border border-border/60 bg-background/40 px-2 py-1.5">
                    <p>Final Rating</p>
                    <p className="text-sm font-semibold text-foreground">{(member.avg_final_rating ?? 0).toFixed(2)}</p>
                  </div>
                  <div className="rounded-md border border-border/60 bg-background/40 px-2 py-1.5">
                    <p>Consistency</p>
                    <p className="text-sm font-semibold text-foreground">{(member.consistency_percent ?? 0).toFixed(1)}%</p>
                  </div>
                </div>
              </Card>
            </button>
          ))}
        </section>
      )}

      {!loading && filteredMembers.length === 0 && (
        <Card className="rounded-xl border bg-card p-5">
          <CardDescription>No team members matched your filters.</CardDescription>
        </Card>
      )}
    </motion.div>
  );
}
