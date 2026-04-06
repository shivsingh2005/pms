"use client";

import Link from "next/link";
import { ArrowRight, Building2, CheckCircle2, AlertTriangle, Users } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/dashboard/StatCard";
import { Button } from "@/components/ui/button";
import { useLeadershipPortalData } from "@/hooks/useLeadershipPortalData";

export function LeadershipDashboard() {
  const {
    loading,
    emptyMessage,
    hasAnyData,
    atRiskEmployees,
    summarySnapshot,
    goalCompletionRate,
    aiInsights,
  } = useLeadershipPortalData({ range: "quarter" });

  const nextAction = atRiskEmployees.length > 0
    ? {
        title: "Resolve high-risk talent signals",
        subtitle: `${atRiskEmployees.length} people are in medium or high risk bands.`,
        href: "/leadership/talent-insights",
        label: "Open Talent Insights",
      }
    : {
        title: "Review performance direction",
        subtitle: "Risk is currently controlled. Validate trend direction for next quarter planning.",
        href: "/leadership/performance-trends",
        label: "Open Performance Trends",
      };

  if (loading) {
    return (
      <Card className="rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Loading leadership snapshot</CardTitle>
        <CardDescription>Preparing organization summary and next actions.</CardDescription>
      </Card>
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
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Org Performance"
          value={`${summarySnapshot.avgPerformance.toFixed(1)}%`}
          trendLabel="Current org baseline"
          trend={summarySnapshot.avgPerformance >= 70 ? "up" : "flat"}
          icon={Building2}
        />
        <StatCard
          title="Goal Completion"
          value={`${goalCompletionRate.toFixed(1)}%`}
          trendLabel="Execution readiness"
          trend={goalCompletionRate >= 65 ? "up" : "flat"}
          icon={CheckCircle2}
        />
        <StatCard
          title="Risk Flags"
          value={String(summarySnapshot.atRisk)}
          trendLabel="Employees requiring action"
          trend={summarySnapshot.atRisk > 0 ? "down" : "flat"}
          icon={AlertTriangle}
        />
        <StatCard
          title="Coverage"
          value={`${summarySnapshot.employees} people`}
          trendLabel={`${summarySnapshot.managers} managers`}
          trend="flat"
          icon={Users}
        />
      </section>

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
        <CardTitle>Strategic Signals</CardTitle>
        <CardDescription>Latest synthesized insights from current organization data.</CardDescription>
        <div className="space-y-2">
          {aiInsights.slice(0, 3).map((insight, index) => (
            <p key={`leadership-insight-${index}`} className="rounded-lg border border-border/70 p-3 text-sm text-muted-foreground">
              {insight}
            </p>
          ))}
        </div>
      </Card>
    </div>
  );
}
