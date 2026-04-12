"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { MetricChart } from "@/components/dashboard/MetricChart";
import { resolveTrainingFocus, summarizeTopTrainingFocus } from "@/lib/training-focus";
import { hrService } from "@/services/hr";
import { useSessionStore } from "@/store/useSessionStore";
import type { HROrgAnalytics, HROverview } from "@/types";

export default function HRAnalyticsPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);
  const [overview, setOverview] = useState<HROverview | null>(null);
  const [analytics, setAnalytics] = useState<HROrgAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

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
  }, [router, user]);

  const trainingNeedSummary = useMemo(() => {
    const rows = overview?.training_heatmap ?? [];
    const counts = new Map<string, number>();
    rows.forEach((row) => {
      counts.set(row.training_need_level, (counts.get(row.training_need_level) ?? 0) + 1);
    });
    return ["No Need", "Low", "Medium", "High", "Critical"].map((label) => ({
      label,
      value: counts.get(label) ?? 0,
    }));
  }, [overview?.training_heatmap]);

  const topTrainingFocus = useMemo(() => {
    const focuses = (overview?.training_heatmap ?? [])
      .filter((row) => row.needs_training)
      .map((row) =>
        resolveTrainingFocus({
          progress: Number(row.progress ?? 0),
          consistency: Number(row.consistency ?? 0),
          rating: Number(row.rating ?? 0),
          needsTraining: Boolean(row.needs_training),
        }),
      );
    return summarizeTopTrainingFocus(focuses);
  }, [overview?.training_heatmap]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="HR Analytics"
        description="Organization trends, distribution signals, and training demand for deeper decision support."
      />

      {loading ? (
        <Card className="rounded-xl border bg-card p-5">
          <CardDescription>Loading analytics...</CardDescription>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Card className="rounded-xl border bg-card p-5">
            <CardTitle>Performance Trend</CardTitle>
            <CardDescription>Average organizational performance over recent periods.</CardDescription>
            <div className="mt-4">
              <MetricChart kind="line" data={analytics?.performance_trend ?? []} xKey="week" yKey="value" color="#2563EB" />
            </div>
          </Card>

          <Card className="rounded-xl border bg-card p-5">
            <CardTitle>Department Comparison</CardTitle>
            <CardDescription>Department-level performance average for current snapshot.</CardDescription>
            <div className="mt-4">
              <MetricChart kind="bar" data={analytics?.department_comparison ?? []} xKey="department" yKey="value" color="#10B981" />
            </div>
          </Card>

          <Card className="rounded-xl border bg-card p-5">
            <CardTitle>Rating Distribution</CardTitle>
            <CardDescription>Distribution of employee ratings across the organization.</CardDescription>
            <div className="mt-4">
              <MetricChart kind="bar" data={analytics?.rating_distribution ?? []} xKey="label" yKey="count" color="#F59E0B" />
            </div>
          </Card>

          <Card className="rounded-xl border bg-card p-5">
            <CardTitle>Check-in Consistency</CardTitle>
            <CardDescription>Trend of check-in consistency over time.</CardDescription>
            <div className="mt-4">
              <MetricChart kind="line" data={analytics?.checkin_consistency ?? []} xKey="week" yKey="value" color="#EF4444" />
            </div>
          </Card>

          <Card className="rounded-xl border bg-card p-5 xl:col-span-2">
            <CardTitle>Training Need Distribution</CardTitle>
            <CardDescription>Derived from current heatmap levels. Most needed training type: {topTrainingFocus}.</CardDescription>
            <div className="mt-4">
              <MetricChart
                kind="bar"
                data={trainingNeedSummary}
                xKey="label"
                yKey="value"
                color="#0EA5E9"
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
      )}
    </motion.div>
  );
}
