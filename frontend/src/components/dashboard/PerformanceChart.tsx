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
      className="rounded-xl border border-border bg-card"
    >
      <MetricChart kind="line" data={data} xKey="week" yKey="value" />
    </ChartCard>
  );
}
