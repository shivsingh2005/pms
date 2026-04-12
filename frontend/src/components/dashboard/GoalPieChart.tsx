"use client";

import { LazyPieChart } from "@/components/charts";

import { ChartCard } from "@/components/dashboard/ChartCard";

interface GoalPieChartProps {
  data: { name: string; value: number }[];
}

const COLORS = [
  "#4F46E5",
  "#7C3AED",
  "#EC4899",
  "#06B6D4",
  "#10B981",
  "#F59E0B",
  "#EF4444",
];

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid hsl(var(--border))",
  backgroundColor: "hsl(var(--card))",
  color: "hsl(var(--foreground))",
  padding: "10px 12px",
  boxShadow: "var(--shadow-md)",
};

export function GoalPieChart({ data }: GoalPieChartProps) {
  const safeData = data.length ? data : [];

  return (
    <ChartCard
      title="Goal Distribution"
      description="Rating distribution across review labels"
      className="rounded-xl border border-border bg-card"
    >
      <div className="h-64 rounded-xl border border-border bg-surface p-4 shadow-soft">
        {safeData.length ? (
          <LazyPieChart
            data={safeData}
            dataKey="value"
            nameKey="name"
            innerRadius={52}
            outerRadius={86}
            colors={COLORS}
            tooltipStyle={chartTooltipStyle}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">No data available</div>
        )}
      </div>
    </ChartCard>
  );
}
