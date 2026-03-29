"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertTriangle, CalendarClock, Filter, TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { MetricChart } from "@/components/dashboard/MetricChart";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeadershipPortalData, type LeadershipTimeRange } from "@/hooks/useLeadershipPortalData";
import { useSessionStore } from "@/store/useSessionStore";

const RANGE_OPTIONS: Array<{ value: LeadershipTimeRange; label: string }> = [
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "quarter", label: "Quarter" },
];

export default function LeadershipPerformanceTrendsPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  const [range, setRange] = useState<LeadershipTimeRange>("month");
  const [department, setDepartment] = useState<string>("");
  const [managerId, setManagerId] = useState<string>("");

  const {
    loading,
    hasAnyData,
    emptyMessage,
    departments,
    managers,
    orgProgressTrend,
    departmentComparison,
    underperformingTrend,
    checkinFrequencyTrend,
    aiInsights,
  } = useLeadershipPortalData({ range, department, managerId });

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  const managerOptions = useMemo(() => {
    if (!department) return managers;
    return managers.filter((manager) => (manager.department || "") === department);
  }, [department, managers]);

  useEffect(() => {
    if (managerId && !managerOptions.some((manager) => manager.id === managerId)) {
      setManagerId("");
    }
  }, [managerId, managerOptions]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Performance Trends</h1>
        <p className="text-sm text-muted-foreground">Strategic trend intelligence for performance, risk drift, and check-in velocity.</p>
      </div>

      <Card className="rounded-2xl border border-border/75 bg-gradient-to-r from-blue-500/10 via-emerald-500/10 to-amber-500/10">
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 text-sm text-foreground">
            <Filter className="h-4 w-4 text-blue-600" />
            Filters
          </div>
          <select
            value={range}
            onChange={(event) => setRange(event.target.value as LeadershipTimeRange)}
            className="h-10 rounded-lg border border-border/70 bg-card px-3 text-sm text-foreground"
          >
            {RANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select
            value={department}
            onChange={(event) => setDepartment(event.target.value)}
            className="h-10 rounded-lg border border-border/70 bg-card px-3 text-sm text-foreground"
          >
            <option value="">All Departments</option>
            {departments.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
          <select
            value={managerId}
            onChange={(event) => setManagerId(event.target.value)}
            className="h-10 rounded-lg border border-border/70 bg-card px-3 text-sm text-foreground"
          >
            <option value="">All Managers</option>
            {managerOptions.map((manager) => (
              <option key={manager.id} value={manager.id}>
                {manager.name}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {loading ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
        </div>
      ) : !hasAnyData ? (
        <Card className="rounded-2xl border border-dashed border-border/80 bg-card/70 text-center">
          <CardTitle>Performance Data Unavailable</CardTitle>
          <CardDescription className="mt-2">{emptyMessage}</CardDescription>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Org Performance Trend</CardTitle>
              <CardDescription>Blue gradient tracks monthly execution health.</CardDescription>
              <div className="mt-4">
                <MetricChart kind="line" data={orgProgressTrend} xKey="period" yKey="value" color="#2563EB" />
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Department Comparison</CardTitle>
              <CardDescription>Department-wise performance comparison for prioritization.</CardDescription>
              <div className="mt-4">
                <MetricChart
                  kind="bar"
                  data={departmentComparison}
                  xKey="department"
                  yKey="value"
                  color="#10B981"
                  barPalette={{
                    Engineering: "#2563EB",
                    Sales: "#10B981",
                    Marketing: "#F59E0B",
                    Operations: "#EF4444",
                  }}
                />
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Underperforming Trend</CardTitle>
              <CardDescription>Red curve highlights widening performance pressure.</CardDescription>
              <div className="mt-4">
                <MetricChart kind="area" data={underperformingTrend} xKey="period" yKey="value" color="#EF4444" />
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Check-in Frequency Trend</CardTitle>
              <CardDescription>Consistency rhythm from check-in activity over time.</CardDescription>
              <div className="mt-4">
                <MetricChart kind="line" data={checkinFrequencyTrend} xKey="period" yKey="value" color="#F59E0B" />
              </div>
            </Card>
          </div>

          <Card className="rounded-2xl border border-border/75 bg-gradient-to-r from-blue-500/10 via-yellow-500/10 to-red-500/10">
            <CardTitle className="text-base">Actionable Insights</CardTitle>
            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
              {aiInsights.map((insight, index) => (
                <div key={`trend-insight-${index}`} className="rounded-lg border border-border/60 bg-card/80 p-3 text-sm text-muted-foreground">
                  {index === 0 ? <TrendingUp className="mr-2 inline h-3.5 w-3.5 text-blue-600" /> : null}
                  {index === 1 ? <AlertTriangle className="mr-2 inline h-3.5 w-3.5 text-red-500" /> : null}
                  {index === 2 ? <TrendingDown className="mr-2 inline h-3.5 w-3.5 text-amber-500" /> : null}
                  {index === 3 ? <CalendarClock className="mr-2 inline h-3.5 w-3.5 text-emerald-600" /> : null}
                  {insight}
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </motion.div>
  );
}
