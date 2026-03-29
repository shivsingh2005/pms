"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

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
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(17,24,39,0.95)",
  color: "#E5E7EB",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
};

export function GoalPieChart({ data }: GoalPieChartProps) {
  const safeData = data.length ? data : [];

  return (
    <ChartCard
      title="Goal Distribution"
      description="Rating distribution across review labels"
      className="rounded-2xl border border-border/75 bg-card/95"
    >
      <div className="h-64 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
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
              <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-[#9CA3AF]">No Data Available</div>
        )}
      </div>
    </ChartCard>
  );
}
