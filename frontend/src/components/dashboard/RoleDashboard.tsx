"use client";

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

const trend = [
  { name: "Q1", score: 72 },
  { name: "Q2", score: 76 },
  { name: "Q3", score: 81 },
  { name: "Q4", score: 84 },
];

const velocity = [
  { name: "W1", score: 68 },
  { name: "W2", score: 74 },
  { name: "W3", score: 79 },
  { name: "W4", score: 83 },
];

const distribution = [
  { name: "EE", value: 12 },
  { name: "DE", value: 22 },
  { name: "ME", value: 43 },
  { name: "SME", value: 18 },
  { name: "NI", value: 5 },
];

export function RoleDashboard({ role }: { role: UserRole }) {
  if (role === "employee") {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Goals Completed" value="14" trendLabel="+12% this quarter" trend="up" icon={Goal} className="h-28 rounded-xl p-4" />
          <StatCard title="Consistency" value="91%" trendLabel="3-week streak" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
          <StatCard title="Review Readiness" value="High" trendLabel="No blockers" trend="flat" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Peer Signals" value="18" trendLabel="2 new mentions" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ProgressCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="My Progress" value={78} />
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
                <p className="mt-1 text-sm text-muted-foreground">Execution consistency has improved over the last 4 weeks.</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Focus Area</p>
                <p className="mt-1 text-sm text-muted-foreground">Increase weekly check-in completion to reduce review-cycle risk.</p>
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
          <StatCard title="Team Goals" value="26" trendLabel="+6 this cycle" trend="up" icon={Goal} className="h-28 rounded-xl p-4" />
          <StatCard title="Avg Consistency" value="84%" trendLabel="+3 points" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
          <StatCard title="At-Risk Goals" value="5" trendLabel="-2 this week" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Active Reports" value="11" trendLabel="steady" trend="flat" icon={Users} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Team Progress Heatmap</CardTitle>
            <div className="mt-4">
              <HeatmapGrid values={[65, 72, 90, 44, 85, 78, 66, 81, 88, 62, 58, 74, 79, 92]} />
            </div>
          </DashboardCard>
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Stack Ranking</CardTitle>
            <div className="mt-4">
              <StackRankingTable rows={[{ name: "Ariana", score: 91, trend: "up" }, { name: "Rahul", score: 87, trend: "up" }, { name: "Karan", score: 79, trend: "flat" }, { name: "Meera", score: 74, trend: "down" }]} />
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
                <p className="mt-1 text-sm text-muted-foreground">Prioritize weekly feedback for lower-ranked performers.</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Team Momentum</p>
                <p className="mt-1 text-sm text-muted-foreground">Progress trend indicates sustained delivery improvement.</p>
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
          <StatCard title="Review Cycles" value="4" trendLabel="on schedule" trend="flat" icon={Radar} className="h-28 rounded-xl p-4" />
          <StatCard title="Calibration Drift" value="7%" trendLabel="-1.5%" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
          <StatCard title="Training Requests" value="32" trendLabel="+8 this month" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
          <StatCard title="Completion Rate" value="89%" trendLabel="+2 points" trend="up" icon={Activity} className="h-28 rounded-xl p-4" />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ChartCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="Rating Calibration">
            <MetricChart kind="bar" data={distribution} xKey="name" yKey="value" color="hsl(var(--secondary))" className="h-[240px]" />
          </ChartCard>
          <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
            <CardTitle>Training Need Heatmap</CardTitle>
            <div className="mt-4">
              <HeatmapGrid values={[30, 45, 61, 53, 29, 71, 88, 67, 50, 39, 64, 75, 82, 40]} />
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
                <p className="mt-1 text-sm text-muted-foreground">Increase calibration checks in teams with higher variance.</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-surface/45 p-4">
                <p className="text-sm font-medium text-foreground">Enablement</p>
                <p className="mt-1 text-sm text-muted-foreground">Expand targeted training for teams with repeated risk signals.</p>
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
        <StatCard title="Org Health" value="87" trendLabel="+4 points" trend="up" icon={Radar} className="h-28 rounded-xl p-4" />
        <StatCard title="Cycle Completion" value="93%" trendLabel="steady" trend="flat" icon={Activity} className="h-28 rounded-xl p-4" />
        <StatCard title="Risk Flags" value="6" trendLabel="-2 this week" trend="down" icon={Gauge} className="h-28 rounded-xl p-4" />
        <StatCard title="Leadership Signals" value="12" trendLabel="+1 this week" trend="up" icon={Users} className="h-28 rounded-xl p-4" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ChartCard className="min-h-[320px] rounded-xl p-6 shadow-sm" title="Company Performance Trends">
          <MetricChart kind="area" data={trend} xKey="name" yKey="score" color="hsl(var(--secondary))" className="h-[240px]" />
        </ChartCard>
        <DashboardCard className="min-h-[320px] rounded-xl p-6 shadow-sm">
          <CardTitle>Talent Pipeline Snapshot</CardTitle>
          <div className="mt-4">
            <StackRankingTable rows={[{ name: "High Potential Pool", score: 26, trend: "up" }, { name: "Succession Ready", score: 14, trend: "flat" }, { name: "Attrition Risk", score: 8, trend: "down" }]} />
          </div>
        </DashboardCard>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <DashboardCard className="rounded-xl p-6 shadow-sm">
          <CardTitle>Operating Momentum</CardTitle>
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <StatCard title="Delivery Pace" value="92" trendLabel="+3 points" trend="up" icon={Activity} className="h-full" />
            <StatCard title="Retention Outlook" value="Stable" trendLabel="flat" trend="flat" icon={Gauge} className="h-full" />
            <StatCard title="Escalations" value="3" trendLabel="-1 this week" trend="down" icon={Radar} className="h-full" />
          </div>
        </DashboardCard>
      </div>
    </div>
  );
}
