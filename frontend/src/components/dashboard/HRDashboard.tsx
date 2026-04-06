"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowRight, Building2, Users } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/dashboard/StatCard";
import { Button } from "@/components/ui/button";
import { hrService } from "@/services/hr";
import type { HROrgAnalytics, HROverview } from "@/types";

export function HRDashboard() {
  const [overview, setOverview] = useState<HROverview | null>(null);
  const [analytics, setAnalytics] = useState<HROrgAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      hrService.getOverview().catch(() => null),
      hrService.getOrgAnalytics().catch(() => null),
    ])
      .then(([overviewPayload, analyticsPayload]) => {
        setOverview(overviewPayload);
        setAnalytics(analyticsPayload);
      })
      .finally(() => setLoading(false));
  }, []);

  const riskRows = useMemo(() => {
    const cells = overview?.training_heatmap ?? [];
    return [...cells]
      .sort((a, b) => {
        const score = (level: string) => {
          if (level === "Critical") return 4;
          if (level === "High") return 3;
          if (level === "Medium") return 2;
          if (level === "Low") return 1;
          return 0;
        };
        return score(b.training_need_level) - score(a.training_need_level);
      })
      .slice(0, 3);
  }, [overview?.training_heatmap]);

  const hasRisk = (overview?.at_risk_employees ?? 0) > 0;
  const nextAction = hasRisk
    ? {
        title: "Run focused risk intervention",
        subtitle: `${overview?.at_risk_employees ?? 0} employees are currently marked at risk.`,
        href: "/hr/employee-directory",
        label: "Open Employee Directory",
      }
    : {
        title: "Review org analytics",
        subtitle: "No urgent alerts. Validate trend health and prepare calibration actions.",
        href: "/hr/analytics",
        label: "Open HR Analytics",
      };

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Employees"
          value={String(overview?.total_employees ?? 0)}
          trendLabel="Current directory size"
          trend="flat"
          icon={Users}
        />
        <StatCard
          title="Total Managers"
          value={String(overview?.total_managers ?? 0)}
          trendLabel="Reporting leaders"
          trend="flat"
          icon={Building2}
        />
        <StatCard
          title="At-Risk Employees"
          value={String(overview?.at_risk_employees ?? 0)}
          trendLabel="Needs intervention"
          trend={hasRisk ? "down" : "flat"}
          icon={AlertTriangle}
        />
        <StatCard
          title="Avg Org Performance"
          value={`${overview?.avg_org_performance ?? 0}%`}
          trendLabel="Organization snapshot"
          trend={(overview?.avg_org_performance ?? 0) >= 70 ? "up" : "flat"}
          icon={Building2}
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

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Priority Employees</CardTitle>
          <CardDescription>Top three training-need signals from the latest heatmap snapshot.</CardDescription>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading risk signals...</p>
          ) : riskRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No risk signals available.</p>
          ) : (
            riskRows.map((row) => (
              <div key={row.employee_id} className="rounded-lg border border-border/70 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{row.employee_name}</p>
                  <span className="text-xs text-muted-foreground">{row.training_need_level}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Progress {row.progress.toFixed(1)}% · Consistency {row.consistency.toFixed(1)}%
                </p>
              </div>
            ))
          )}
        </Card>

        <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Snapshot Insight</CardTitle>
          <CardDescription>
            {analytics?.department_comparison.length
              ? "Department comparison is stable. Use analytics for deeper trend investigation."
              : "Analytics data is still warming up. Continue monitoring daily submissions."}
          </CardDescription>
          <Link href="/hr/analytics">
            <Button variant="outline" className="gap-2">
              View Trend Analytics
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}

