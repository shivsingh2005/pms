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
      className="rounded-2xl border border-border/75 bg-card/95"
    >
      <MetricChart kind="bar" data={data} xKey="week" yKey="value" color="hsl(var(--warning))" />
    </ChartCard>
  );
}
