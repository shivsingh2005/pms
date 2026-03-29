"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { managerService } from "@/services/manager";
import { api } from "@/services/api";
import { useSessionStore } from "@/store/useSessionStore";
import { MetricChart } from "@/components/dashboard/MetricChart";
import type { ManagerTeamPerformancePayload } from "@/types";

const emptyPayload: ManagerTeamPerformancePayload = {
  avg_progress: 0,
  completed_goals: 0,
  consistency: 0,
  at_risk: 0,
  trend: [],
  distribution: [
    { label: "EE", count: 0 },
    { label: "DE", count: 0 },
    { label: "ME", count: 0 },
    { label: "SME", count: 0 },
    { label: "NI", count: 0 },
  ],
  workload: [],
  performers: { top: [], low: [] },
  insights: [],
};

function StatCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <Card className="rounded-xl border bg-card p-5">
      <CardDescription>{title}</CardDescription>
      <p className="mt-1 text-3xl font-semibold text-foreground">{value}</p>
      <p className="mt-2 text-xs text-muted-foreground">{subtitle}</p>
    </Card>
  );
}

export default function ManagerTeamPerformancePage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);

  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<ManagerTeamPerformancePayload>(emptyPayload);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, router, setActiveMode, user]);

  useEffect(() => {
    if (!user || activeMode !== "manager") return;

    const loadTeamPerformance =
      typeof managerService.getTeamPerformance === "function"
        ? () => managerService.getTeamPerformance()
        : async () => {
            const { data } = await api.get<ManagerTeamPerformancePayload>("/manager/team-performance");
            return data;
          };

    setLoading(true);
    loadTeamPerformance()
      .then((response) => {
        console.log("team-performance-response", response);
        setPayload(response);
      })
      .catch(() => toast.error("Failed to load team performance analytics"))
      .finally(() => setLoading(false));
  }, [activeMode, user]);

  const trendChartData = useMemo(
    () => payload.trend.map((item, idx) => ({ week: item.week || `Week ${idx + 1}`, progress: item.progress })),
    [payload.trend],
  );

  const distributionChartData = useMemo(
    () => payload.distribution.map((item) => ({ rating: item.label, count: item.count })),
    [payload.distribution],
  );

  const workloadChartData = useMemo(
    () => payload.workload.map((item) => ({ employee: item.employee_name, total_weightage: item.total_weightage })),
    [payload.workload],
  );

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Team Performance"
        description="Live team analytics with trends, risks, rating distribution, and workload visibility."
      />

      {loading && (
        <Card className="rounded-xl border bg-card p-5">
          <CardDescription>Loading team analytics...</CardDescription>
        </Card>
      )}

      {!loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
            <StatCard title="Team Average Progress" value={`${payload.avg_progress}%`} subtitle="Average goal progress across direct reports" />
            <StatCard title="Goals Completed" value={`${payload.completed_goals}`} subtitle="Goals at 100% completion" />
            <StatCard title="Consistency Score" value={`${payload.consistency}%`} subtitle="Recorded check-ins vs expected baseline" />
            <StatCard title="At-Risk Employees" value={`${payload.at_risk}`} subtitle="Employees with avg progress below 40%" />
          </div>

          <div className="grid grid-cols-1 gap-6">
            <Card className="rounded-xl border bg-card p-5">
              <CardTitle>Performance Trend</CardTitle>
              <CardDescription>Weekly average team progress</CardDescription>
              <div className="mt-4">
                <MetricChart
                  kind="line"
                  data={trendChartData}
                  xKey="week"
                  yKey="progress"
                  className="h-[320px]"
                />
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6">
            <Card className="rounded-xl border bg-card p-5">
              <CardTitle>Rating Distribution</CardTitle>
              <CardDescription>Latest employee bands: EE, DE, ME, SME, NI</CardDescription>
              <div className="mt-4">
                <MetricChart
                  kind="bar"
                  data={distributionChartData}
                  xKey="rating"
                  yKey="count"
                  className="h-[320px]"
                />
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card className="rounded-xl border bg-card p-5">
              <CardTitle>Workload Distribution</CardTitle>
              <CardDescription>Total goal weightage by employee</CardDescription>
              <div className="mt-4">
                <MetricChart
                  kind="bar"
                  data={workloadChartData}
                  xKey="employee"
                  yKey="total_weightage"
                  className="h-[320px]"
                />
              </div>
            </Card>

            <Card className="rounded-xl border bg-card p-5 space-y-4">
              <CardTitle>Top vs Low Performers</CardTitle>
              <CardDescription>Progress-based performer segmentation</CardDescription>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-border/70 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Top Performers (&gt; 80%)</p>
                  <div className="mt-2 space-y-2">
                    {payload.performers.top.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No top performers in current snapshot.</p>
                    ) : (
                      payload.performers.top.map((row) => (
                        <div key={row.employee_id} className="flex items-center justify-between gap-2 text-sm">
                          <span className="font-medium text-foreground">{row.employee_name}</span>
                          <span className="text-success">{row.progress}%</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="rounded-lg border border-border/70 p-3">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Low Performers (&lt; 40%)</p>
                  <div className="mt-2 space-y-2">
                    {payload.performers.low.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No low performers in current snapshot.</p>
                    ) : (
                      payload.performers.low.map((row) => (
                        <div key={row.employee_id} className="flex items-center justify-between gap-2 text-sm">
                          <span className="font-medium text-foreground">{row.employee_name}</span>
                          <span className="text-error">{row.progress}%</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {payload.insights.length > 0 && (
            <Card className="rounded-xl border bg-card p-5">
              <CardTitle>AI Insights</CardTitle>
              <CardDescription>Auto-generated performance summary</CardDescription>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                {payload.insights.map((line, idx) => (
                  <p key={idx} className="rounded-md border border-border/70 px-3 py-2 text-sm text-foreground">
                    {line}
                  </p>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </motion.div>
  );
}
