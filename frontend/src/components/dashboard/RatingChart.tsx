"use client";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { MetricChart } from "@/components/dashboard/MetricChart";

interface RatingChartProps {
  data: { week: string; value: number }[];
}

export function RatingChart({ data }: RatingChartProps) {
  return (
    <ChartCard
      title="Rating Trend"
      description="Weekly average rating progression"
      className="rounded-xl border border-border bg-card"
    >
      <MetricChart kind="bar" data={data} xKey="week" yKey="value" color="hsl(var(--warning))" />
    </ChartCard>
  );
}
