"use client";

import { useEffect, useState } from "react";
import { Activity, Gauge, Goal, Radar, Users } from "lucide-react";
import { CardTitle } from "@/components/ui/card";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { HeatmapGrid } from "@/components/dashboard/HeatmapGrid";
import { MetricChart } from "@/components/dashboard/MetricChart";
import { ProgressCard } from "@/components/dashboard/ProgressCard";
import { StackRankingTable } from "@/components/dashboard/StackRankingTable";
import { StatCard } from "@/components/dashboard/StatCard";
import type { UserRole } from "@/types";
import { dashboardService, type DashboardOverview } from "@/services/dashboard";

const emptyOverview: DashboardOverview = {
  role: "employee",
  kpi: {},
  trend: [],
  velocity: [],
  distribution: [],
  heatmap: [],
  stack_ranking: [],
  insights: { primary: "No data available.", secondary: "Start by creating goals and check-ins." },
};

export function RoleDashboard({ role }: { role: UserRole }) {
  const [overview, setOverview] = useState<DashboardOverview>(emptyOverview);

  useEffect(() => {
    dashboardService
      .getOverview()
      .then(setOverview)
      .catch(() => setOverview(emptyOverview));
  }, []);

  const trend = overview.trend;
  const velocity = overview.velocity;
  const distribution = overview.distribution;
  const hasData =
    trend.length > 0 ||
    velocity.length > 0 ||
    distribution.length > 0 ||
    overview.heatmap.length > 0 ||
    overview.stack_ranking.length > 0 ||
    Object.values(overview.kpi ?? {}).some((value) => Number(value ?? 0) > 0);

  if (!hasData) {
    return (
      <DashboardCard className="rounded-xl p-6 shadow-sm">
        <CardTitle>No data available</CardTitle>
        <p className="mt-2 text-sm text-muted-foreground">Start by creating goals to unlock check-ins, meetings, and ratings.</p>
      </DashboardCard>
    );
  }

  if (role === "employee") {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Goals Completed" value={String(overview.kpi.goals_completed ?? 0)} trendLabel="from database" trend="up" icon={Goal} className="h-28 rounded-xl p-4" />
          <StatCard title="Consistency" value={`${overview.kpi.consistency ?? 0}%`} trendLabel="check-in completion" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
          <StatCard title="Review Readiness" value={overview.kpi.review_readiness ?? "Low"} trendLabel="derived from progress" trend="flat" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Peer Signals" value={String(overview.kpi.peer_signals ?? 0)} trendLabel="ratings received" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ProgressCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="My Progress" value={overview.kpi.consistency ?? 0} />
          <ChartCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="Performance Trend">
            <MetricChart kind="line" data={trend} xKey="name" yKey="score" className="h-[240px]" />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <ChartCard className="min-h-[350px] rounded-xl p-6 shadow-sm" title="Weekly Velocity">
            <MetricChart kind="bar" data={velocity} xKey="name" yKey="score" color="hsl(var(--secondary))" className="h-[260px]" />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <ChartCard className="rounded-xl p-6 shadow-sm" title="Progress Distribution" description="Current quarter outcomes by rating bucket.">
            <MetricChart kind="bar" data={distribution} xKey="name" yKey="value" color="hsl(var(--primary))" className="h-[260px]" />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <DashboardCard className="rounded-xl p-6 shadow-sm">
            <CardTitle>Insights</CardTitle>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Strength</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.primary}</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Focus Area</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.secondary}</p>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    );
  }

  if (role === "manager") {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Team Goals" value={String(overview.kpi.team_goals ?? 0)} trendLabel="from database" trend="up" icon={Goal} className="h-28 rounded-xl p-4" />
          <StatCard title="Avg Consistency" value={`${overview.kpi.consistency ?? 0}%`} trendLabel="check-in completion" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
          <StatCard title="At-Risk Goals" value={String(overview.kpi.at_risk_goals ?? 0)} trendLabel="progress below threshold" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Active Reports" value={String(overview.kpi.active_reports ?? 0)} trendLabel="direct reports" trend="flat" icon={Users} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Team Progress Heatmap</CardTitle>
            <div className="mt-4">
              <HeatmapGrid values={overview.heatmap.length ? overview.heatmap : [0]} />
            </div>
          </DashboardCard>
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Stack Ranking</CardTitle>
            <div className="mt-4">
              <StackRankingTable rows={overview.stack_ranking} />
            </div>
          </DashboardCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <ChartCard className="min-h-[350px] rounded-xl p-6 shadow-sm" title="Team Performance Trend">
            <MetricChart kind="line" data={trend} xKey="name" yKey="score" className="h-[260px]" />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <DashboardCard className="rounded-xl p-6 shadow-sm">
            <CardTitle>Manager Insights</CardTitle>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Coaching Opportunity</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.primary}</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Team Momentum</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.secondary}</p>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    );
  }

  if (role === "hr") {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Org Health" value={String(overview.kpi.org_health ?? 0)} trendLabel="from org data" trend="flat" icon={Radar} className="h-28 rounded-xl p-4" />
          <StatCard title="Risk Flags" value={String(overview.kpi.risk_flags ?? 0)} trendLabel="low-progress goals" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Leadership Signals" value={String(overview.kpi.leadership_signals ?? 0)} trendLabel="review records" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
          <StatCard title="Completion Rate" value={`${overview.kpi.cycle_completion ?? 0}%`} trendLabel="goal completion" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ChartCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="Rating Calibration">
            <MetricChart kind="bar" data={distribution} xKey="name" yKey="value" color="hsl(var(--secondary))" className="h-[240px]" />
          </ChartCard>
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Training Need Heatmap</CardTitle>
            <div className="mt-4">
              <HeatmapGrid values={overview.heatmap.length ? overview.heatmap : [0]} />
            </div>
          </DashboardCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <ChartCard className="rounded-xl p-6 shadow-sm" title="Quarter Distribution" description="Organization-wide rating distribution for current quarter.">
            <MetricChart kind="line" data={trend} xKey="name" yKey="score" className="h-[260px]" />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <DashboardCard className="rounded-xl p-6 shadow-sm">
            <CardTitle>HR Insights</CardTitle>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Policy Focus</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.primary}</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Enablement</p>
                <p className="mt-1 text-sm text-muted-foreground">{overview.insights.secondary}</p>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Org Health" value={String(overview.kpi.org_health ?? 0)} trendLabel="from database" trend="up" icon={Radar} className="h-28 rounded-xl p-4" />
        <StatCard title="Cycle Completion" value={`${overview.kpi.cycle_completion ?? 0}%`} trendLabel="goal closure" trend="flat" icon={Activity} className="h-28 rounded-xl p-4" />
        <StatCard title="Risk Flags" value={String(overview.kpi.risk_flags ?? 0)} trendLabel="low progress detected" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
        <StatCard title="Leadership Signals" value={String(overview.kpi.leadership_signals ?? 0)} trendLabel="review and trend signals" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ChartCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="Company Performance Trends">
          <MetricChart kind="area" data={trend} xKey="name" yKey="score" color="hsl(var(--secondary))" className="h-[240px]" />
        </ChartCard>
        <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
          <CardTitle>Talent Pipeline Snapshot</CardTitle>
          <div className="mt-4">
            <StackRankingTable rows={overview.stack_ranking} />
          </div>
        </DashboardCard>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <DashboardCard className="rounded-xl p-6 shadow-sm">
          <CardTitle>Operating Momentum</CardTitle>
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <StatCard title="Delivery Pace" value={String(overview.kpi.org_health ?? 0)} trendLabel="organization progress" trend="up" icon={Activity} className="h-full" />
            <StatCard title="Retention Outlook" value={overview.kpi.risk_flags && overview.kpi.risk_flags > 10 ? "Watch" : "Stable"} trendLabel="risk-weighted" trend="flat" icon={Gauge} className="h-full" />
            <StatCard title="Escalations" value={String(overview.kpi.risk_flags ?? 0)} trendLabel="from risk flags" trend="down" icon={Radar} className="h-full" />
          </div>
        </DashboardCard>
      </div>
    </div>
  );
}
