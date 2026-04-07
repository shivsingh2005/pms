"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Users } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { managerService } from "@/services/manager";
import type { ManagerTeamMember } from "@/types";
import type { ManagerTeamPerformancePayload } from "@/types";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/dashboard/StatCard";
import { useSessionStore } from "@/store/useSessionStore";

const DEFAULT_MANAGER_DASHBOARD: ManagerTeamPerformancePayload = {
  team_size: 0,
  avg_performance: 0,
  avg_progress: 0,
  completed_goals: 0,
  consistency: 0,
  at_risk: 0,
  message: "No team data available.",
  trend: [],
  distribution: [
    { label: "EE", count: 0 },
    { label: "DE", count: 0 },
    { label: "ME", count: 0 },
    { label: "SME", count: 0 },
    { label: "NI", count: 0 },
  ],
  workload: [],
  performers: {
    top: [],
    low: [],
  },
  top_performers: [],
  low_performers: [],
  team: [],
  insights: ["No performance signals available yet."],
};

function buildFallbackDashboard(team: ManagerTeamMember[]): ManagerTeamPerformancePayload {
  if (!team.length) {
    return DEFAULT_MANAGER_DASHBOARD;
  }

  const normalizedTeam = team.map((member) => ({
    employee_id: member.id,
    employee_name: member.name,
    progress: member.goal_progress_percent,
    rating: member.avg_final_rating,
    consistency: member.consistency_percent,
  }));
  const avgProgress = normalizedTeam.reduce((sum, member) => sum + member.progress, 0) / normalizedTeam.length;
  const avgConsistency = normalizedTeam.reduce((sum, member) => sum + member.consistency, 0) / normalizedTeam.length;
  const avgRating = normalizedTeam.reduce((sum, member) => sum + member.rating, 0) / normalizedTeam.length;
  const top = [...normalizedTeam].sort((a, b) => b.progress - a.progress).slice(0, 3);
  const low = [...normalizedTeam].sort((a, b) => a.progress - b.progress).slice(0, 3);

  return {
    team_size: normalizedTeam.length,
    avg_performance: Number(avgRating.toFixed(2)),
    avg_progress: Number(avgProgress.toFixed(1)),
    completed_goals: team.reduce((sum, member) => sum + member.current_goals_count, 0),
    consistency: Number(avgConsistency.toFixed(1)),
    at_risk: normalizedTeam.filter((member) => member.progress < 50 || member.rating <= 2).length,
    message: "Showing computed fallback from team snapshot.",
    trend: [],
    distribution: [
      { label: "EE", count: 0 },
      { label: "DE", count: 0 },
      { label: "ME", count: 0 },
      { label: "SME", count: 0 },
      { label: "NI", count: 0 },
    ],
    workload: team.map((member) => ({
      employee_id: member.id,
      employee_name: member.name,
      total_weightage: member.current_workload,
    })),
    performers: { top, low },
    top_performers: top,
    low_performers: low,
    team: normalizedTeam,
    insights: ["Fallback mode active: displaying team-derived dashboard metrics."],
  };
}

export function ManagerDashboard() {
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);
  const [dashboardData, setDashboardData] = useState<ManagerTeamPerformancePayload | null>(null);
  const [team, setTeam] = useState<ManagerTeamMember[]>([]);
  const [pendingCheckinsCount, setPendingCheckinsCount] = useState(0);
  const [pendingProposalsCount, setPendingProposalsCount] = useState(0);
  const [pendingGoalsCount, setPendingGoalsCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "manager" && activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, setActiveMode, user]);

  useEffect(() => {
    if (!user || user.role !== "manager" || activeMode !== "manager") {
      setDashboardData(null);
      setTeam([]);
      setPendingCheckinsCount(0);
      setPendingGoalsCount(0);
      setPendingProposalsCount(0);
      return;
    }

    let cancelled = false;
    setLoading(true);

    const managerId = user.id;
    Promise.allSettled([
      managerService.getDashboard(managerId, { silent: true }),
      managerService.getTeam({ silent: true }),
    ])
      .then(([dashboardResult, teamResult]) => {
        if (cancelled) {
          return;
        }

        const teamPayload = teamResult.status === "fulfilled" ? teamResult.value : [];
        if (teamResult.status === "fulfilled") {
          setTeam(teamResult.value);
        } else {
          setTeam([]);
        }

        if (dashboardResult.status === "fulfilled") {
          setDashboardData(dashboardResult.value);
          setLoadError(null);
        } else {
          // Fallback to legacy manager analytics endpoint if strict dashboard route fails.
          managerService
            .getTeamPerformance({ silent: true })
            .then((fallbackPayload) => {
              if (cancelled) return;
              setDashboardData(fallbackPayload);
              setLoadError(null);
            })
            .catch(() => {
              if (cancelled) return;
              setDashboardData(buildFallbackDashboard(teamPayload));
              setLoadError("Live dashboard unavailable. Showing fallback data.");
            });
        }

        setTimeout(() => {
          if (cancelled) return;

          Promise.allSettled([
            managerService.getPendingCheckins({ silent: true }),
            managerService.getPendingMeetingProposals({ silent: true }),
          ]).then(([pendingCheckinsResult, proposalsResult]) => {
            if (cancelled) return;

            if (pendingCheckinsResult.status === "fulfilled") {
              setPendingCheckinsCount(pendingCheckinsResult.value.length);
            } else {
              setPendingCheckinsCount(0);
            }

            setPendingGoalsCount(
              teamPayload.filter((member) => member.status === "At Risk").length,
            );

            if (proposalsResult.status === "fulfilled") {
              setPendingProposalsCount(proposalsResult.value.length);
            } else {
              setPendingProposalsCount(0);
            }
          });
        }, 120);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeMode, user]);

  const pendingApprovalsCount = pendingCheckinsCount + pendingGoalsCount + pendingProposalsCount;

  if (!user || user.role !== "manager") {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Manager mode required</CardTitle>
        <CardDescription>Only manager accounts can view this dashboard.</CardDescription>
      </Card>
    );
  }

  if (activeMode !== "manager") {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Switching to manager mode</CardTitle>
        <CardDescription>Preparing manager data context.</CardDescription>
      </Card>
    );
  }

  const hasTeam = (dashboardData?.team_size ?? 0) > 0;
  const topAttention = [...team]
    .sort((a, b) => a.goal_progress_percent - b.goal_progress_percent)
    .slice(0, 3);
  const nextAction = pendingApprovalsCount > 0
    ? {
        title: "Review pending approvals",
        subtitle: `${pendingApprovalsCount} approvals are waiting for your decision.`,
        href: "/manager/approvals",
        label: "Open Approvals",
      }
    : (dashboardData?.at_risk ?? 0) > 0
      ? {
          title: "Address at-risk team members",
          subtitle: `${dashboardData?.at_risk ?? 0} team members need intervention this week.`,
          href: "/manager/team-dashboard",
          label: "Open Team Dashboard",
        }
      : {
          title: "Review team analytics",
          subtitle: "Use deeper trends to prepare your next 1:1 planning pass.",
          href: "/manager/team-performance",
          label: "Open Analytics",
        };

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Active Reports"
          value={String(dashboardData?.team_size ?? team.length)}
          trendLabel="Direct reports"
          trend="flat"
          icon={Users}
        />
        <StatCard
          title="Goals Completed"
          value={String(dashboardData?.completed_goals ?? 0)}
          trendLabel="Team completion"
          trend={(dashboardData?.completed_goals ?? 0) > 0 ? "up" : "flat"}
          icon={Users}
        />
        <StatCard
          title="At-Risk"
          value={String(dashboardData?.at_risk ?? 0)}
          trendLabel="Needs intervention"
          trend={(dashboardData?.at_risk ?? 0) > 0 ? "down" : "flat"}
          icon={Users}
        />
        <StatCard
          title="Pending Approvals"
          value={String(pendingApprovalsCount)}
          trendLabel={`${pendingCheckinsCount} check-ins · ${pendingProposalsCount} meetings`}
          trend={pendingApprovalsCount > 0 ? "down" : "flat"}
          icon={Users}
        />
      </section>

      {loading && (
        <Card className="space-y-2">
          <CardTitle>Loading manager dashboard</CardTitle>
          <CardDescription>Fetching team snapshot data.</CardDescription>
        </Card>
      )}

      {loadError && !loading && (
        <Card className="space-y-2">
          <CardTitle>Dashboard unavailable</CardTitle>
          <CardDescription>{loadError}</CardDescription>
        </Card>
      )}

      <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>{nextAction.title}</CardTitle>
        <CardDescription>{nextAction.subtitle}</CardDescription>
        <Link href={nextAction.href}>
          <Button className="gap-2">
            {nextAction.label}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </Card>

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Immediate Attention</CardTitle>
        <CardDescription>Top three team members who may need coaching this week.</CardDescription>
        {!topAttention.length ? (
          <p className="text-sm text-muted-foreground">No team members are currently flagged.</p>
        ) : (
          topAttention.map((member) => (
            <div key={member.id} className="rounded-lg border border-border/70 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground">{member.name}</p>
                <span className="text-xs text-muted-foreground">{member.goal_progress_percent}%</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{member.department} · {member.consistency_percent}% consistency</p>
            </div>
          ))
        )}
      </Card>

      {!loading && !hasTeam && (
        <Card className="space-y-2">
          <CardTitle>No team assigned</CardTitle>
          <CardDescription>{dashboardData?.message || "No direct reports are assigned to this manager yet."}</CardDescription>
        </Card>
      )}

      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Manager Insight</CardTitle>
        <CardDescription>{dashboardData?.insights?.[0] || "No AI insight available yet."}</CardDescription>
      </Card>
    </div>
  );
}
