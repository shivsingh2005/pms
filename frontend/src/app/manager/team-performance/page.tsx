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
import type { ManagerStackRankingPayload, ManagerTeamPerformancePayload } from "@/types";
import { Button } from "@/components/ui/button";

const emptyPayload: ManagerTeamPerformancePayload = {
  team_size: 0,
  avg_performance: 0,
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
  top_performers: [],
  low_performers: [],
  team: [],
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
  const [rankingLoading, setRankingLoading] = useState(false);
  const [ranking, setRanking] = useState<ManagerStackRankingPayload | null>(null);
  const [sortBy, setSortBy] = useState<"progress" | "rating" | "consistency">("progress");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [atRiskOnly, setAtRiskOnly] = useState(false);
  const [limit, setLimit] = useState(10);

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
        console.warn("team-performance-response", response);
        setPayload(response);
      })
      .catch(() => toast.error("Failed to load team performance analytics"))
      .finally(() => setLoading(false));
  }, [activeMode, user]);

  useEffect(() => {
    if (!user || activeMode !== "manager") return;

    setRankingLoading(true);
    managerService
      .getStackRanking({
        sort_by: sortBy,
        order,
        at_risk_only: atRiskOnly,
        limit,
      })
      .then((response) => setRanking(response))
      .catch(() => toast.error("Failed to load stack ranking"))
      .finally(() => setRankingLoading(false));
  }, [activeMode, atRiskOnly, limit, order, sortBy, user]);

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
            <StatCard title="At-Risk Employees" value={`${payload.at_risk}`} subtitle="Employees with progress under 50% or rating <= 2" />
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

            <Card className="rounded-xl border bg-card p-5 space-y-4">
              <CardTitle>Stack Ranking Controls</CardTitle>
              <CardDescription>Sort by progress, rating, or consistency and control risk visibility.</CardDescription>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                <label className="space-y-1 text-sm">
                  <span className="text-xs text-muted-foreground">Sort By</span>
                  <select
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={sortBy}
                    onChange={(event) => setSortBy(event.target.value as "progress" | "rating" | "consistency")}
                  >
                    <option value="progress">Progress</option>
                    <option value="rating">Rating</option>
                    <option value="consistency">Consistency</option>
                  </select>
                </label>
                <label className="space-y-1 text-sm">
                  <span className="text-xs text-muted-foreground">Order</span>
                  <select
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={order}
                    onChange={(event) => setOrder(event.target.value as "asc" | "desc")}
                  >
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </select>
                </label>
                <label className="space-y-1 text-sm">
                  <span className="text-xs text-muted-foreground">Top N</span>
                  <input
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    type="number"
                    min={1}
                    max={100}
                    value={limit}
                    onChange={(event) => {
                      const value = Number(event.target.value || 10);
                      setLimit(Math.max(1, Math.min(100, value)));
                    }}
                  />
                </label>
                <label className="flex items-end gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={atRiskOnly}
                    onChange={(event) => setAtRiskOnly(event.target.checked)}
                  />
                  <span>At-risk only</span>
                </label>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setSortBy("progress");
                  setOrder("desc");
                  setAtRiskOnly(false);
                  setLimit(10);
                }}
              >
                Reset Controls
              </Button>
            </Card>
          </div>

          <Card className="rounded-xl border bg-card p-5 space-y-4">
            <CardTitle>Stack Ranking</CardTitle>
            <CardDescription>
              Ranked list for visibility and decision support. Showing {ranking?.items.length ?? 0} of {ranking?.total_considered ?? 0} members.
            </CardDescription>

            {rankingLoading ? (
              <p className="text-sm text-muted-foreground">Loading stack ranking...</p>
            ) : !ranking || ranking.items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No ranking data available for current filters.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border/70 text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-2 py-2">Rank</th>
                      <th className="px-2 py-2">Employee</th>
                      <th className="px-2 py-2">Progress</th>
                      <th className="px-2 py-2">Rating</th>
                      <th className="px-2 py-2">Consistency</th>
                      <th className="px-2 py-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranking.items.map((item) => (
                      <tr key={item.employee_id} className="border-b border-border/50">
                        <td className="px-2 py-2 font-medium text-foreground">#{item.rank}</td>
                        <td className="px-2 py-2 text-foreground">{item.employee_name}</td>
                        <td className="px-2 py-2 text-foreground">{item.progress}%</td>
                        <td className="px-2 py-2 text-foreground">{item.rating}</td>
                        <td className="px-2 py-2 text-foreground">{item.consistency}%</td>
                        <td className="px-2 py-2">
                          <span
                            className={`rounded-full px-2 py-1 text-xs font-medium ${
                              item.risk_level === "high"
                                ? "bg-red-100 text-red-700"
                                : item.risk_level === "medium"
                                  ? "bg-amber-100 text-amber-700"
                                  : "bg-emerald-100 text-emerald-700"
                            }`}
                          >
                            {item.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

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

