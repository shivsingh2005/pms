"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Briefcase, CheckCircle2, ListChecks, Target } from "lucide-react";
import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/dashboard/StatCard";
import { Button } from "@/components/ui/button";
import { dashboardService, type EmployeeDashboardData } from "@/services/dashboard";
import { aiService } from "@/services/ai";
import { goalsService } from "@/services/goals";
import { useSessionStore } from "@/store/useSessionStore";
import type { Goal } from "@/types";

const EMPTY_EMPLOYEE_DASHBOARD: EmployeeDashboardData = {
  progress: 0,
  completed_goals: 0,
  active_goals: 0,
  checkins_count: 0,
  last_checkin: null,
  consistency_percent: 0,
  manager_name: null,
  manager_email: null,
  manager_title: null,
  review_readiness: "Low",
  checkin_status: "Missed",
  trend: [
    { week: "W1", value: 0 },
    { week: "W2", value: 0 },
    { week: "W3", value: 0 },
    { week: "W4", value: 0 },
    { week: "W5", value: 0 },
    { week: "W6", value: 0 },
  ],
  consistency: [
    { week: "W1", value: 0 },
    { week: "W2", value: 0 },
    { week: "W3", value: 0 },
    { week: "W4", value: 0 },
    { week: "W5", value: 0 },
    { week: "W6", value: 0 },
  ],
};

export function EmployeeDashboard() {
  const user = useSessionStore((state) => state.user);
  const [overview, setOverview] = useState<EmployeeDashboardData>(EMPTY_EMPLOYEE_DASHBOARD);
  const [growthSuggestion, setGrowthSuggestion] = useState<string>("AI growth suggestions will appear here.");
  const [focusGoals, setFocusGoals] = useState<Goal[]>([]);

  useEffect(() => {
    dashboardService.getEmployeeDashboard().then(setOverview).catch(() => setOverview(EMPTY_EMPLOYEE_DASHBOARD));
    goalsService
      .getGoals()
      .then((items) => {
        const prioritized = [...items]
          .sort((a, b) => Number(a.progress) - Number(b.progress))
          .slice(0, 3);
        setFocusGoals(prioritized);
      })
      .catch(() => setFocusGoals([]));
  }, []);

  useEffect(() => {
    if (!user) {
      return;
    }

    aiService
      .growthSuggestion({
        role: user.title || user.role,
        department: user.department || "General",
        current_skills: ["execution", "collaboration"],
        target_role: user.title || "Senior Contributor",
      })
      .then((payload) => {
        const plan = Array.isArray(payload?.next_quarter_plan) ? payload.next_quarter_plan.join(" ") : "";
        if (plan.trim()) {
          setGrowthSuggestion(plan);
        }
      })
      .catch(() => null);
  }, [user]);

  const lastCheckinLabel = overview.last_checkin ? new Date(overview.last_checkin).toLocaleDateString() : "No check-ins yet";
  const managerName = overview.manager_name || "Not assigned";
  const managerEmail = overview.manager_email || "No manager email";
  const managerTitle = overview.manager_title || "Manager";
  const nextAction = overview.checkin_status !== "On Track"
    ? {
        title: "Submit your next check-in",
        subtitle: "Your manager needs your latest progress update.",
        href: "/checkins",
        label: "Open Check-ins",
      }
    : overview.active_goals === 0
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
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Overall Progress"
          value={`${overview.progress.toFixed(1)}%`}
          trendLabel="Goal execution"
          trend={overview.progress >= 70 ? "up" : overview.progress >= 45 ? "flat" : "down"}
          icon={Target}
        />
        <StatCard
          title="Goals Completed"
          value={String(overview.completed_goals)}
          trendLabel={`${overview.active_goals} active goals`}
          trend={overview.completed_goals > 0 ? "up" : "flat"}
          icon={CheckCircle2}
        />
        <StatCard
          title="Total Check-ins"
          value={String(overview.checkins_count)}
          trendLabel={overview.checkin_status}
          trend={overview.checkin_status === "On Track" ? "up" : "down"}
          icon={ListChecks}
        />
        <StatCard
          title="Consistency"
          value={`${overview.consistency_percent.toFixed(1)}%`}
          trendLabel="Check-in consistency"
          trend={overview.consistency_percent >= 70 ? "up" : overview.consistency_percent >= 45 ? "flat" : "down"}
          icon={ListChecks}
        />
      </div>

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
          <p className="text-xs text-muted-foreground">Last check-in: {lastCheckinLabel}</p>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Goal Focus</CardTitle>
          <CardDescription>Three goals that currently need the most attention.</CardDescription>
          {focusGoals.length === 0 ? (
            <p className="text-sm text-muted-foreground">No goals available yet.</p>
          ) : (
            <div className="space-y-2">
              {focusGoals.map((goal) => (
                <div key={goal.id} className="rounded-lg border border-border/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-foreground">{goal.title}</p>
                    <span className="text-xs text-muted-foreground">{goal.progress}%</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{goal.status} · {goal.framework}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle className="inline-flex items-center gap-2">
            <Briefcase className="h-4 w-4" />
            Manager And Growth Support
          </CardTitle>
          <CardDescription>
            {managerName} ({managerTitle}) · {managerEmail}
          </CardDescription>
          <p className="text-sm text-muted-foreground">{growthSuggestion}</p>
          <Link href="/employee/growth">
            <Button variant="outline" className="gap-2">
              Open Growth Hub
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </Card>
      </div>

      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Review Readiness</CardTitle>
        <CardDescription>Current status: {overview.review_readiness}</CardDescription>
      </Card>
    </div>
  );
}
