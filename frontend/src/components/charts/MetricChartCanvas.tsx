"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface MetricChartCanvasProps {
  kind: "area" | "bar" | "line";
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKey: string;
  color: string;
  barPalette?: Record<string, string>;
  chartTooltipStyle: Record<string, string | number>;
  gradientId: string;
}

const CHART_COLORS = {
  blue: "hsl(var(--primary))",
  purple: "#7C3AED",
};

export function MetricChartCanvas({
  kind,
  data,
  xKey,
  yKey,
  color,
  barPalette,
  chartTooltipStyle,
  gradientId,
}: MetricChartCanvasProps) {
  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
      {kind === "area" ? (
        <AreaChart data={data}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.blue} stopOpacity={0.8} />
              <stop offset="100%" stopColor={CHART_COLORS.purple} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="3 4" />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <Tooltip
            cursor={{ stroke: "hsl(var(--border))", strokeDasharray: "4 4" }}
            contentStyle={chartTooltipStyle}
            labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600, marginBottom: 4 }}
          />
          <Area type="monotone" dataKey={yKey} stroke={CHART_COLORS.blue} strokeWidth={3} fill={`url(#${gradientId})`} isAnimationActive animationDuration={350} />
        </AreaChart>
      ) : kind === "line" ? (
        <LineChart data={data}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor={CHART_COLORS.blue} />
              <stop offset="100%" stopColor={CHART_COLORS.purple} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="3 4" />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <Tooltip
            cursor={{ stroke: "hsl(var(--border))", strokeDasharray: "4 4" }}
            contentStyle={chartTooltipStyle}
            labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600, marginBottom: 4 }}
          />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={`url(#${gradientId})`}
            strokeWidth={3}
            dot={{ r: 4, fill: CHART_COLORS.blue, stroke: "hsl(var(--card))", strokeWidth: 2 }}
            activeDot={{ r: 6, fill: CHART_COLORS.purple, stroke: "hsl(var(--card))", strokeWidth: 2 }}
            isAnimationActive
            animationDuration={350}
          />
        </LineChart>
      ) : (
        <BarChart data={data}>
          <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="3 4" />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <Tooltip
            cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
            contentStyle={chartTooltipStyle}
            labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600, marginBottom: 4 }}
          />
          <Bar dataKey={yKey} fill={color} radius={[8, 8, 8, 8]} isAnimationActive animationDuration={350}>
            {data.map((entry, index) => {
              const paletteKey = String(entry[xKey]);
              const barColor = barPalette?.[paletteKey] || color;
              return <Cell key={`bar-cell-${index}`} fill={barColor} />;
            })}
          </Bar>
        </BarChart>
      )}
    </ResponsiveContainer>
  );
}
