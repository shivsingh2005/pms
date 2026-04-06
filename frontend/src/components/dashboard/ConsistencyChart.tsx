"use client";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { MetricChart } from "@/components/dashboard/MetricChart";

interface ConsistencyChartProps {
  data: { week: string; value: number }[];
}

export function ConsistencyChart({ data }: ConsistencyChartProps) {
  return (
    <ChartCard
      title="Check-in Consistency"
      description="Check-ins recorded per week"
      className="rounded-xl border border-border bg-card"
    >
      <MetricChart kind="bar" data={data} xKey="week" yKey="value" color="hsl(var(--success))" />
    </ChartCard>
  );
}
