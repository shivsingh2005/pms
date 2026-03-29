"use client";

import { useEffect, useState } from "react";
import { Activity, Award, CheckCircle2, ListChecks } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/dashboard/StatCard";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { RatingChart } from "@/components/dashboard/RatingChart";
import { GoalPieChart } from "@/components/dashboard/GoalPieChart";
import { ConsistencyChart } from "@/components/dashboard/ConsistencyChart";
import { dashboardService, type EmployeeDashboardData } from "@/services/dashboard";
import { aiService } from "@/services/ai";
import { useSessionStore } from "@/store/useSessionStore";

const EMPTY_EMPLOYEE_DASHBOARD: EmployeeDashboardData = {
  progress: 0,
  completed_goals: 0,
  active_goals: 0,
  avg_rating: 0,
  latest_rating: 0,
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
  ratings: [
    { week: "W1", value: 0 },
    { week: "W2", value: 0 },
    { week: "W3", value: 0 },
    { week: "W4", value: 0 },
    { week: "W5", value: 0 },
    { week: "W6", value: 0 },
  ],
  distribution: [],
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

  useEffect(() => {
    dashboardService.getEmployeeDashboard().then(setOverview).catch(() => setOverview(EMPTY_EMPLOYEE_DASHBOARD));
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
        const plan = Array.isArray(payload?.development_plan) ? payload.development_plan.join(" ") : "";
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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Overall Progress"
          value={`${overview.progress.toFixed(1)}%`}
          trendLabel="Goal execution"
          trend={overview.progress >= 70 ? "up" : overview.progress >= 45 ? "flat" : "down"}
          icon={Activity}
        />
        <StatCard
          title="Goals Completed"
          value={String(overview.completed_goals)}
          trendLabel={`${overview.active_goals} active goals`}
          trend={overview.completed_goals > 0 ? "up" : "flat"}
          icon={CheckCircle2}
        />
        <StatCard
          title="Average Rating"
          value={overview.avg_rating.toFixed(2)}
          trendLabel={`Latest ${overview.latest_rating.toFixed(2)}`}
          trend={overview.avg_rating >= 4 ? "up" : overview.avg_rating >= 3 ? "flat" : "down"}
          icon={Award}
        />
        <StatCard
          title="Total Check-ins"
          value={String(overview.checkins_count)}
          trendLabel={overview.checkin_status}
          trend={overview.checkin_status === "On Track" ? "up" : "down"}
          icon={ListChecks}
        />
      </div>

      <div className="grid grid-cols-1">
        <PerformanceChart data={overview.trend} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <RatingChart data={overview.ratings} />
        <GoalPieChart data={overview.distribution} />
      </div>

      <div className="grid grid-cols-1">
        <ConsistencyChart data={overview.consistency} />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>My Goals</CardTitle>
          <CardDescription>{overview.completed_goals} completed | {overview.active_goals} active</CardDescription>
        </Card>
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>My Progress</CardTitle>
          <CardDescription>{overview.progress.toFixed(1)}% overall | {overview.consistency_percent.toFixed(1)}% consistency</CardDescription>
        </Card>
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>My Check-ins</CardTitle>
          <CardDescription>{overview.checkins_count} check-ins completed | Last: {lastCheckinLabel} | {overview.checkin_status}</CardDescription>
        </Card>
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>My Reviews</CardTitle>
          <CardDescription>Latest rating: {overview.latest_rating.toFixed(2)} | Readiness: {overview.review_readiness}</CardDescription>
        </Card>
        <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95 md:col-span-2 xl:col-span-4">
          <CardTitle>My Manager</CardTitle>
          <CardDescription>
            {managerName} ({managerTitle}) | {managerEmail}
          </CardDescription>
        </Card>
      </div>

      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>AI Growth Suggestions</CardTitle>
        <CardDescription>{growthSuggestion}</CardDescription>
      </Card>
    </div>
  );
}
