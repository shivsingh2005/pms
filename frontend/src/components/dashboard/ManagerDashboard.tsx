"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Users } from "lucide-react";
import { toast } from "sonner";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/shared/StatCard";
import { useAuth } from "@/context/AuthContext";
import { goalsService } from "@/services/goals";
import { useManagerDashboard } from "@/hooks/useDashboardData";
import { fixed } from "@/lib/safe";
import { safeArray, safeNumber } from "@/lib/safeData";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import type { ManagerPendingGoal } from "@/types";

export function ManagerDashboard() {
  const { user } = useAuth();
  const { data: dashboardData, loading, error, refetch } = useManagerDashboard();
  const [pendingGoals, setPendingGoals] = useState<ManagerPendingGoal[]>([]);
  const [goalComments, setGoalComments] = useState<Record<string, string>>({});
  const [approvingGoalId, setApprovingGoalId] = useState<string | null>(null);

  useEffect(() => {
    if (!user || user.role !== "manager") {
      setPendingGoals([]);
      return;
    }

    goalsService
      .getManagerPendingGoals()
      .then((items) => setPendingGoals(items))
      .catch(() => setPendingGoals([]));
  }, [user]);

  // Safety checks
  if (!user || user.role !== "manager") {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Manager mode required</CardTitle>
        <CardDescription>Only manager accounts can view this dashboard.</CardDescription>
      </Card>
    );
  }

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error && !dashboardData) {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Failed to load dashboard</CardTitle>
        <CardDescription>{error}</CardDescription>
        <Button onClick={refetch} variant="outline">
          Try Again
        </Button>
      </Card>
    );
  }

  // Safe data access
  const teamSize = safeNumber(dashboardData.team_size, 0);
  const completedGoals = safeNumber(dashboardData.completed_goals ?? 0, 0);
  const atRisk = safeNumber(dashboardData.at_risk, 0);
  const avgPerformance = safeNumber(dashboardData.avg_performance, 0);
  const team = safeArray(dashboardData.team);

  const topAttention = team
    .slice()
    .sort((a, b) => {
      const aProgress = safeNumber((a as any)?.progress, 0);
      const bProgress = safeNumber((b as any)?.progress, 0);
      return aProgress - bProgress;
    })
    .slice(0, 3);

  const pendingApprovalsCount = safeNumber(dashboardData.pending_approvals, 0);

  const refreshPendingGoals = async () => {
    try {
      const items = await goalsService.getManagerPendingGoals();
      setPendingGoals(items);
    } catch {
      toast.error("Failed to refresh goal approvals");
    }
  };

  const decideGoal = async (goalId: string, action: "approve" | "request-edit" | "reject") => {
    const comment = goalComments[goalId]?.trim();
    if (action === "reject" && !comment) {
      toast.error("Rejection reason is required");
      return;
    }

    setApprovingGoalId(goalId);
    try {
      if (action === "approve") {
        await goalsService.managerApproveGoal(goalId, comment || undefined);
      } else if (action === "request-edit") {
        await goalsService.managerRequestEdit(goalId, comment || undefined);
      } else {
        await goalsService.managerRejectGoal(goalId, comment);
      }

      setGoalComments((prev) => ({ ...prev, [goalId]: "" }));
      await Promise.all([refreshPendingGoals(), refetch()]);
      toast.success("Goal decision saved");
    } catch {
      toast.error("Unable to save goal decision");
    } finally {
      setApprovingGoalId(null);
    }
  };

  const nextAction =
    pendingApprovalsCount > 0
      ? {
          title: "Review pending approvals",
          subtitle: `${pendingApprovalsCount} approvals are waiting for your decision.`,
          href: "/manager/approvals",
          label: "Open Approvals",
        }
      : atRisk > 0
        ? {
            title: "Address at-risk team members",
            subtitle: `${atRisk} team members need intervention this week.`,
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
      {/* Stat Cards */}
      <StatCardsSection
        teamSize={teamSize}
        completedGoals={completedGoals}
        atRisk={atRisk}
        avgPerformance={avgPerformance}
      />

      {/* Next Action */}
      <NextActionSection nextAction={nextAction} />

      <GoalApprovalsSection
        pendingGoals={pendingGoals}
        goalComments={goalComments}
        approvingGoalId={approvingGoalId}
        onCommentChange={(goalId, value) => setGoalComments((prev) => ({ ...prev, [goalId]: value }))}
        onDecideGoal={decideGoal}
      />

      {/* Top Attention */}
      <ErrorBoundary componentName="TopAttention">
        <TopAttentionSection topAttention={topAttention} />
      </ErrorBoundary>

      {/* Empty State or Insight */}
      {teamSize === 0 ? (
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>No team assigned</CardTitle>
          <CardDescription>No direct reports are assigned to this manager yet.</CardDescription>
        </Card>
      ) : (
        <ErrorBoundary componentName="Insight">
          <InsightSection insight={dashboardData.insights?.[0]} />
        </ErrorBoundary>
      )}
    </div>
  );
}

// Sub-component: Stat Cards
function StatCardsSection({ teamSize, completedGoals, atRisk, avgPerformance }: any) {
  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <StatCard
        title="Active Reports"
        value={String(teamSize)}
        trendLabel="Direct reports"
        trend="flat"
        icon={Users}
      />
      <StatCard
        title="Goals Completed"
        value={String(completedGoals)}
        trendLabel="Team completion"
        trend={completedGoals > 0 ? "up" : "flat"}
        icon={Users}
      />
      <StatCard
        title="At-Risk"
        value={String(atRisk)}
        trendLabel="Needs intervention"
        trend={atRisk > 0 ? "down" : "flat"}
        icon={Users}
      />
      <StatCard
        title="Performance"
        value={fixed(avgPerformance, 1)}
        trendLabel="Team average"
        trend={avgPerformance > 3 ? "up" : "flat"}
        icon={Users}
      />
    </section>
  );
}

// Sub-component: Next Action
function NextActionSection({ nextAction }: any) {
  return (
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
  );
}

function GoalApprovalsSection({
  pendingGoals,
  goalComments,
  approvingGoalId,
  onCommentChange,
  onDecideGoal,
}: {
  pendingGoals: ManagerPendingGoal[];
  goalComments: Record<string, string>;
  approvingGoalId: string | null;
  onCommentChange: (goalId: string, value: string) => void;
  onDecideGoal: (goalId: string, action: "approve" | "request-edit" | "reject") => void;
}) {
  const preview = pendingGoals.slice(0, 3);

  return (
    <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Goal Approvals</CardTitle>
          <CardDescription>
            Self-created employee goals stay in review until you approve them, and employees cannot submit check-ins before approval.
          </CardDescription>
        </div>
        <Link href="/manager/approvals">
          <Button variant="outline">Open full approvals queue</Button>
        </Link>
      </div>

      {pendingGoals.length === 0 ? (
        <p className="text-sm text-muted-foreground">No self-created goals are waiting for approval.</p>
      ) : (
        <div className="space-y-3">
          {preview.map((item) => (
            <div key={item.goal.id} className="space-y-3 rounded-xl border border-border/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-foreground">{item.goal.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.employee_name} ({item.employee_role}) · {item.employee_department || "General"}
                  </p>
                </div>
                <span className="rounded-full border border-border/70 px-2 py-1 text-xs text-muted-foreground">
                  {item.goal.weightage}%
                </span>
              </div>
              {item.goal.description ? <p className="text-xs text-muted-foreground">{item.goal.description}</p> : null}
              <textarea
                className="min-h-[80px] w-full rounded-xl border border-border bg-background p-3 text-sm outline-none transition focus:border-primary"
                placeholder="Manager comment"
                value={goalComments[item.goal.id] || ""}
                onChange={(event) => onCommentChange(item.goal.id, event.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <Button size="sm" onClick={() => onDecideGoal(item.goal.id, "approve")} disabled={approvingGoalId === item.goal.id}>
                  Approve
                </Button>
                <Button size="sm" variant="secondary" onClick={() => onDecideGoal(item.goal.id, "request-edit")} disabled={approvingGoalId === item.goal.id}>
                  Request edit
                </Button>
                <Button size="sm" variant="outline" onClick={() => onDecideGoal(item.goal.id, "reject")} disabled={approvingGoalId === item.goal.id}>
                  Reject
                </Button>
              </div>
            </div>
          ))}
          {pendingGoals.length > preview.length ? (
            <p className="text-xs text-muted-foreground">{pendingGoals.length - preview.length} more goals are waiting in the full queue.</p>
          ) : null}
        </div>
      )}
    </Card>
  );
}

function TopAttentionSection({ topAttention }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>Immediate Attention</CardTitle>
      <CardDescription>Top three team members who may need coaching this week.</CardDescription>
      {!topAttention || topAttention.length === 0 ? (
        <p className="text-sm text-muted-foreground">No team members are currently flagged.</p>
      ) : (
        topAttention.map((member: any) => (
          <div key={member.id || member.employee_id} className="rounded-lg border border-border/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">
                {member.name || member.employee_name || "Unknown"}
              </p>
              <span className="text-xs text-muted-foreground">
                {safeNumber(member.progress ?? member.goal_progress_percent, 0)}%
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {member.department || "N/A"} · {safeNumber(member.consistency, 0)}% consistency
            </p>
          </div>
        ))
      )}
    </Card>
  );
}

function InsightSection({ insight }: any) {
  return (
    <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>Manager Insight</CardTitle>
      <CardDescription>{insight || "No AI insight available yet."}</CardDescription>
    </Card>
  );
}
