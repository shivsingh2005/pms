"use client";

import { AlertTriangle, Building2, CheckCircle2, Sparkles, TrendingUp, Users } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { MetricChart } from "@/components/dashboard/MetricChart";
import { StatCard } from "@/components/dashboard/StatCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeadershipPortalData } from "@/hooks/useLeadershipPortalData";

const RISK_COLORS = ["#10B981", "#F59E0B", "#EF4444"];

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(17,24,39,0.95)",
  color: "#E5E7EB",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
};

export function LeadershipDashboard() {
  const {
    loading,
    emptyMessage,
    hasAnyData,
    orgProgressTrend,
    goalCompletionRate,
    riskDistribution,
    topPerformers,
    trainingNeedSummary,
    summarySnapshot,
    aiInsights,
  } = useLeadershipPortalData({ range: "quarter" });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={`leadership-stat-skeleton-${index}`} className="h-28 w-full rounded-2xl bg-white/5" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Skeleton className="h-72 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-72 w-full rounded-2xl bg-white/5" />
        </div>
      </div>
    );
  }

  if (!hasAnyData) {
    return (
      <Card className="rounded-2xl border border-dashed border-border/80 bg-card/70 text-center">
        <CardTitle>Leadership Insights Unavailable</CardTitle>
        <CardDescription className="mt-2">{emptyMessage}</CardDescription>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Org Performance"
          value={`${summarySnapshot.avgPerformance.toFixed(1)}%`}
          trendLabel="Blue zone: delivery momentum"
          trend="up"
          icon={Building2}
          className="bg-gradient-to-br from-blue-500/20 via-blue-500/5 to-transparent"
        />
        <StatCard
          title="Goal Completion"
          value={`${goalCompletionRate.toFixed(1)}%`}
          trendLabel="Green zone: growth execution"
          trend={goalCompletionRate >= 65 ? "up" : "flat"}
          icon={CheckCircle2}
          className="bg-gradient-to-br from-emerald-500/20 via-emerald-500/5 to-transparent"
        />
        <StatCard
          title="Risk Flags"
          value={String(summarySnapshot.atRisk)}
          trendLabel="Yellow/Red watchlist"
          trend={summarySnapshot.atRisk > 0 ? "down" : "flat"}
          icon={AlertTriangle}
          className="bg-gradient-to-br from-amber-500/20 via-amber-500/5 to-transparent"
        />
        <StatCard
          title="Org Coverage"
          value={`${summarySnapshot.employees} people`}
          trendLabel={`${summarySnapshot.managers} managers connected`}
          trend="flat"
          icon={Users}
          className="bg-gradient-to-br from-rose-500/20 via-rose-500/5 to-transparent"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Org Progress Trend</CardTitle>
          <CardDescription>Blue trendline for organizational performance movement.</CardDescription>
          <div className="mt-4">
            <MetricChart kind="line" data={orgProgressTrend} xKey="period" yKey="value" color="#2563EB" />
          </div>
        </Card>

        <Card className="rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Risk Distribution</CardTitle>
          <CardDescription>Red and yellow clusters indicate immediate intervention areas.</CardDescription>
          <div className="mt-4 h-72 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
            {riskDistribution.some((entry) => entry.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={riskDistribution} dataKey="value" nameKey="name" innerRadius={50} outerRadius={95} paddingAngle={2}>
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`${entry.name}-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">{emptyMessage}</div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Goal Completion Rate</CardTitle>
          <CardDescription>Final rating = average of all check-in ratings after manager-approved meetings.</CardDescription>
          <div className="mt-5 space-y-3">
            <Progress value={goalCompletionRate} className="h-3 bg-muted/60" />
            <p className="text-sm text-muted-foreground">{goalCompletionRate.toFixed(1)}% of tracked goals have reached completion milestone.</p>
          </div>

          <div className="mt-6 space-y-3">
            <h3 className="text-sm font-medium text-foreground">Top Performers Snapshot</h3>
            {topPerformers.length ? (
              topPerformers.map((person) => (
                <div key={person.id} className="rounded-xl border border-border/70 bg-surface/70 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{person.name}</p>
                      <p className="text-xs text-muted-foreground">{person.role}</p>
                    </div>
                    <Badge className="bg-blue-500/10 text-blue-700 ring-blue-400/30">Rating {person.rating.toFixed(2)}</Badge>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">{emptyMessage}</p>
            )}
          </div>
        </Card>

        <Card className="rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Training Need Summary</CardTitle>
          <CardDescription>Heatmap-derived growth priorities for leadership planning.</CardDescription>
          <div className="mt-4">
            <MetricChart
              kind="bar"
              data={trainingNeedSummary}
              xKey="label"
              yKey="value"
              color="#10B981"
              barPalette={{
                "No Need": "#22C55E",
                Low: "#84CC16",
                Medium: "#F59E0B",
                High: "#EF4444",
                Critical: "#B91C1C",
              }}
            />
          </div>
        </Card>
      </div>

      <Card className="rounded-2xl border border-border/75 bg-gradient-to-r from-blue-500/10 via-emerald-500/10 to-amber-500/10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-blue-600" />
          <CardTitle className="text-base">AI Strategic Signals</CardTitle>
        </div>
        <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
          {aiInsights.map((insight, index) => (
            <div key={`leadership-ai-insight-${index}`} className="rounded-lg border border-border/60 bg-card/70 p-3 text-sm text-muted-foreground">
              <TrendingUp className="mr-2 inline h-3.5 w-3.5 text-blue-600" />
              {insight}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
