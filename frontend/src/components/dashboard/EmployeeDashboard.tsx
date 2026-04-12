"use client";

import { ArrowRight, Briefcase, CheckCircle2, ListChecks, Target } from "lucide-react";
import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/shared/StatCard";
import { Button } from "@/components/ui/button";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import { useAuth } from "@/context/AuthContext";
import { useEmployeeDashboard } from "@/hooks/useDashboardData";
import { pct } from "@/lib/safe";
import { safeArray, safeNumber } from "@/lib/safeData";

export function EmployeeDashboard() {
  const { user } = useAuth();
  const { data: dashboardData, loading, error, refetch } = useEmployeeDashboard();

  if (!user || user.role !== "employee") {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Employee mode required</CardTitle>
        <CardDescription>Only employee accounts can view this dashboard.</CardDescription>
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

  const progress = safeNumber(dashboardData.overall_progress, 0);
  const goalsCount = safeNumber(dashboardData.goals_count, 0);
  const checkinsUsed = safeNumber(dashboardData.checkins_used, 0);
  const checkinsTotal = safeNumber(dashboardData.checkins_total, 5);
  const band = dashboardData.band || null;
  const managerName = typeof dashboardData.manager_name === "string" && dashboardData.manager_name.trim()
    ? dashboardData.manager_name
    : "Unassigned";
  const managerEmail = typeof dashboardData.manager_email === "string" && dashboardData.manager_email.trim()
    ? dashboardData.manager_email
    : "Not available";
  const managerTitle = typeof dashboardData.manager_title === "string" && dashboardData.manager_title.trim()
    ? dashboardData.manager_title
    : null;

  const goalsPreview = safeArray(dashboardData.goals_preview);
  const checkinsCount = checkinsUsed;
  const checkinsStatus = checkinsUsed >= checkinsTotal ? "Caught Up" : checkinsUsed > 0 ? "On Track" : "Not Started";

  const nextAction =
    checkinsStatus !== "Caught Up"
      ? {
          title: "Submit your next check-in",
          subtitle: "Your manager needs your latest progress update.",
          href: "/checkins",
          label: "Open Check-ins",
        }
      : goalsCount === 0
        ? {
            title: "Create your first goal",
            subtitle: "Define your priorities for this cycle.",
            href: "/goals",
            label: "Create Goal",
          }
        : {
            title: "Keep momentum on active goals",
            subtitle: "Update progress and remove blockers before your next review.",
            href: "/goals",
            label: "Update Goals",
          };

  return (
    <div className="space-y-6">
      <Card className="rounded-2xl border border-border/75 bg-card/95">
        <CardDescription className="text-sm text-foreground">
          Reporting Manager: <span className="font-semibold">{managerName}</span>
          {managerTitle ? <span className="text-muted-foreground"> ({managerTitle})</span> : null}
        </CardDescription>
      </Card>

      <StatCardsSection
        progress={progress}
        goalsCount={goalsCount}
        checkinsCount={checkinsCount}
      />

      <NextActionSection nextAction={nextAction} checkinsUsed={checkinsUsed} checkinsTotal={checkinsTotal} />

      <ManagerContactSection managerName={managerName} managerEmail={managerEmail} managerTitle={managerTitle} />

      <GoalFocusSection goalsPreview={goalsPreview} />

      <BandAndRatingSection band={band} />
    </div>
  );
}

function ManagerContactSection({ managerName, managerEmail, managerTitle }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95" suppressHydrationWarning>
      <CardTitle>Reporting Manager</CardTitle>
      <CardDescription>Your direct manager for reviews and check-ins.</CardDescription>
      <div className="space-y-1 text-sm text-foreground" suppressHydrationWarning>
        <p className="font-medium">{managerName}</p>
        <p className="text-muted-foreground">{managerEmail}</p>
        {managerTitle && <p className="text-xs text-muted-foreground">{managerTitle}</p>}
      </div>
    </Card>
  );
}

function StatCardsSection({ progress, goalsCount, checkinsCount }: any) {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <StatCard
        title="Overall Progress"
        value={pct(progress, 1)}
        trendLabel="Goal execution"
        trend={progress >= 70 ? "up" : progress >= 45 ? "flat" : "down"}
        icon={Target}
      />
      <StatCard
        title="Active Goals"
        value={String(goalsCount)}
        trendLabel="In progress"
        trend={goalsCount > 0 ? "up" : "flat"}
        icon={CheckCircle2}
      />
      <StatCard
        title="Total Check-ins"
        value={String(checkinsCount)}
        trendLabel="Submitted so far"
        trend={checkinsCount > 0 ? "up" : "down"}
        icon={ListChecks}
      />
    </div>
  );
}

function NextActionSection({ nextAction, checkinsUsed, checkinsTotal }: any) {
  const lastCheckString = `${checkinsUsed}/${checkinsTotal} check-ins submitted`;

  return (
    <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>{nextAction.title}</CardTitle>
      <CardDescription>{nextAction.subtitle}</CardDescription>
      <div className="flex flex-wrap items-center gap-3">
        <Link href={nextAction.href}>
          <Button className="gap-2">
            {nextAction.label}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
        <p className="text-xs text-muted-foreground">{lastCheckString}</p>
      </div>
    </Card>
  );
}

function GoalFocusSection({ goalsPreview }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>Active Goals</CardTitle>
      <CardDescription>Goals that currently need the most attention.</CardDescription>
      {!goalsPreview || goalsPreview.length === 0 ? (
        <p className="text-sm text-muted-foreground">No goals created yet. Create your first goal to get started.</p>
      ) : (
        <div className="space-y-2">
          {goalsPreview.slice(0, 3).map((goal: any, idx: number) => (
            <div key={idx} className="rounded-lg border border-border/70 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground">{goal.title || "Untitled Goal"}</p>
                <span className="text-xs text-muted-foreground">{safeNumber(goal.progress, 0)}%</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {goal.status || "In Progress"} · {goal.framework || "OKR"}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function BandAndRatingSection({ band }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle className="inline-flex items-center gap-2">
        <Briefcase className="h-4 w-4" />
        Performance Status
      </CardTitle>
      <CardDescription>{band ? `Your current band: ${band}` : "No performance data available yet."}</CardDescription>
      <Link href="/employee/growth">
        <Button variant="outline" className="gap-2">
          Open Growth Hub
          <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>
    </Card>
  );
}
