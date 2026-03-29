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
      className="rounded-2xl border border-border/75 bg-card/95"
    >
      <MetricChart kind="bar" data={data} xKey="week" yKey="value" color="hsl(var(--success))" />
    </ChartCard>
  );
}
