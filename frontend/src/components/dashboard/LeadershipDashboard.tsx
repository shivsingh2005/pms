"use client";

import Link from "next/link";
import { ArrowRight, TrendingUp, Users, AlertTriangle } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/shared/StatCard";
import { useAuth } from "@/context/AuthContext";
import { useLeadershipDashboard } from "@/hooks/useDashboardData";
import { fixed } from "@/lib/safe";
import { safeArray, safeNumber } from "@/lib/safeData";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";


export function LeadershipDashboard() {
  const { user } = useAuth();
  const { data: dashboardData, loading, error, refetch } = useLeadershipDashboard();

  // Safety checks
  if (!user || (user.role !== "leadership" && user.role !== "hr")) {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Leadership dashboard required</CardTitle>
        <CardDescription>Only leadership and HR accounts can view this dashboard.</CardDescription>
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
  const orgPerformance = safeNumber(dashboardData.org_performance, 0);
  const highPerformers = safeNumber(dashboardData.high_performers, 0);
  const atRisk = safeNumber(dashboardData.at_risk, 0);

  const aopTotal = safeNumber(dashboardData.aop_progress?.total, 0);
  const aopAchieved = safeNumber(dashboardData.aop_progress?.achieved, 0);

  const topPerformers = safeArray(dashboardData.talent_snapshot?.top_performers);
  const atRiskTalent = safeArray(dashboardData.talent_snapshot?.at_risk);

  const aopProgress = aopTotal > 0 ? Math.round((aopAchieved / aopTotal) * 100) : 0;

  const nextAction =
    atRisk > 0
      ? {
          title: "Review at-risk talent",
          subtitle: `${atRisk} employees flagged as at-risk. Review interventions.`,
          href: "/leadership/talent",
          label: "Open Talent View",
        }
      : aopProgress < 80
        ? {
            title: "Monitor AOP progress",
            subtitle: `Organization is ${aopProgress}% through annual goals. Focus on lagging units.`,
            href: "/leadership/aop",
            label: "Open AOP Dashboard",
          }
        : {
            title: "Review organizational health",
            subtitle: "Organization performing well. Review succession plans and development.",
            href: "/leadership/talent",
            label: "Open Talent View",
          };

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <StatCardsSection
        orgPerformance={orgPerformance}
        aopProgress={aopProgress}
        highPerformers={highPerformers}
        atRisk={atRisk}
      />

      {/* Next Action */}
      <NextActionSection nextAction={nextAction} />

      {/* AOP Progress */}
      <ErrorBoundary componentName="AOPProgress">
        <AOPProgressSection aopAchieved={aopAchieved} aopTotal={aopTotal} aopProgress={aopProgress} />
      </ErrorBoundary>

      {/* Top Performers and At-Risk */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ErrorBoundary componentName="TopPerformers">
          <TopPerformersSection topPerformers={topPerformers} />
        </ErrorBoundary>
        <ErrorBoundary componentName="AtRiskTalent">
          <AtRiskTalentSection atRiskTalent={atRiskTalent} />
        </ErrorBoundary>
      </div>
    </div>
  );
}

// Sub-component: Stat Cards
function StatCardsSection({ orgPerformance, aopProgress, highPerformers, atRisk }: any) {
  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <StatCard
        title="Org Performance"
        value={fixed(orgPerformance, 1)}
        trendLabel="Overall score"
        trend={orgPerformance > 3.5 ? "up" : "flat"}
        icon={TrendingUp}
      />
      <StatCard
        title="AOP Progress"
        value={`${aopProgress}%`}
        trendLabel="Goals achieved"
        trend={aopProgress > 70 ? "up" : "down"}
        icon={TrendingUp}
      />
      <StatCard
        title="Top Performers"
        value={String(highPerformers)}
        trendLabel="High potential talent"
        trend="up"
        icon={Users}
      />
      <StatCard
        title="At-Risk"
        value={String(atRisk)}
        trendLabel="Needs support"
        trend={atRisk > 0 ? "down" : "flat"}
        icon={AlertTriangle}
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

function AOPProgressSection({ aopAchieved, aopTotal, aopProgress }: any) {
  return (
    <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>Annual Operating Plan (AOP) Progress</CardTitle>
      <CardDescription>Organization-wide goal achievement across all units.</CardDescription>

      {aopTotal === 0 ? (
        <p className="text-sm text-muted-foreground">No AOP data available yet.</p>
      ) : (
        <div className="space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-muted-foreground">{aopProgress}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-blue-500" style={{ width: `${aopProgress}%` }}></div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <p className="text-muted-foreground">Achieved</p>
              <p className="text-lg font-semibold">{aopAchieved}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Total Goals</p>
              <p className="text-lg font-semibold">{aopTotal}</p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function TopPerformersSection({ topPerformers }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>Top Performers</CardTitle>
      <CardDescription>High-potential talent to recognize and develop.</CardDescription>

      {!topPerformers || topPerformers.length === 0 ? (
        <p className="text-sm text-muted-foreground">No top performers identified yet.</p>
      ) : (
        topPerformers.slice(0, 5).map((performer: any, idx: number) => (
          <div key={idx} className="rounded-lg border border-border/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">
                {performer.name || performer.employee_name || "Unknown"}
              </p>
              <span className="inline-block rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                ⭐
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {performer.department || "N/A"} · {performer.band || performer.level || "N/A"}
            </p>
          </div>
        ))
      )}
    </Card>
  );
}

function AtRiskTalentSection({ atRiskTalent }: any) {
  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
      <CardTitle>At-Risk Talent</CardTitle>
      <CardDescription>Employees requiring immediate attention and support.</CardDescription>

      {!atRiskTalent || atRiskTalent.length === 0 ? (
        <p className="text-sm text-muted-foreground">No at-risk employees identified.</p>
      ) : (
        atRiskTalent.slice(0, 5).map((employee: any, idx: number) => (
          <div key={idx} className="rounded-lg border border-red-200 bg-red-50 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">
                {employee.name || employee.employee_name || "Unknown"}
              </p>
              <span className="inline-block rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-800">
                ⚠️
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {employee.department || "N/A"} · {employee.risk_reason || "Review needed"}
            </p>
          </div>
        ))
      )}
    </Card>
  );
}
