"use client";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { MetricChart } from "@/components/dashboard/MetricChart";

interface PerformanceChartProps {
  data: { week: string; value: number }[];
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  return (
    <ChartCard
      title="Performance Trend"
      description="Weekly progress movement across recent weeks"
      className="rounded-2xl border border-border/75 bg-card/95"
    >
      <MetricChart kind="line" data={data} xKey="week" yKey="value" />
    </ChartCard>
  );
}
