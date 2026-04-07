"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "@/components/charts/recharts-lazy";

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
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={safeData}
                dataKey="value"
                nameKey="name"
                innerRadius={52}
                outerRadius={86}
                paddingAngle={3}
                stroke="rgba(255,255,255,0.2)"
                strokeWidth={1}
                isAnimationActive
                animationDuration={800}
              >
                {safeData.map((entry, idx) => (
                  <Cell key={`${entry.name}-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600, marginBottom: 4 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">No data available</div>
        )}
      </div>
    </ChartCard>
  );
}
