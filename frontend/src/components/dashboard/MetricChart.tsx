"use client";

import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "@/components/charts/recharts-lazy";

interface MetricChartProps {
  kind: "area" | "bar" | "line";
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKey: string;
  color?: string;
  className?: string;
  barPalette?: Record<string, string>;
}

const CHART_COLORS = {
  blue: "hsl(var(--primary))",
  purple: "#7C3AED",
  pink: "#EC4899",
  cyan: "#06B6D4",
  green: "hsl(var(--success))",
  yellow: "hsl(var(--warning))",
  red: "hsl(var(--error))",
};

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid hsl(var(--border))",
  backgroundColor: "hsl(var(--card))",
  color: "hsl(var(--foreground))",
  padding: "10px 12px",
  boxShadow: "var(--shadow-md)",
};

export function MetricChart({
  kind,
  data,
  xKey,
  yKey,
  color = CHART_COLORS.blue,
  className,
  barPalette,
}: MetricChartProps) {
  if (!data.length) {
    return (
      <div
        className={`h-64 rounded-xl border border-border bg-surface p-4 flex items-center justify-center shadow-soft ${className ?? ""}`}
      >
        <p className="text-sm text-muted-foreground">No data available</p>
      </div>
    );
  }

  const gradientId = `metric-grad-${kind}-${yKey}`.replace(/[^a-zA-Z0-9-_]/g, "");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`h-64 rounded-xl border border-border bg-surface p-4 flex items-center justify-center shadow-soft ${className ?? ""}`}
    >
      <ResponsiveContainer width="100%" height="100%">
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
            <Area type="monotone" dataKey={yKey} stroke={CHART_COLORS.blue} strokeWidth={3} fill={`url(#${gradientId})`} isAnimationActive animationDuration={700} />
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
              animationDuration={750}
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
            <Bar dataKey={yKey} fill={color} radius={[8, 8, 8, 8]} isAnimationActive animationDuration={700}>
              {data.map((entry, index) => {
                const paletteKey = String(entry[xKey]);
                const barColor = barPalette?.[paletteKey] || color;
                return <Cell key={`bar-cell-${index}`} fill={barColor} />;
              })}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  );
}

