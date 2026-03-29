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
} from "recharts";

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
  blue: "#4F46E5",
  purple: "#7C3AED",
  pink: "#EC4899",
  cyan: "#06B6D4",
  green: "#10B981",
  yellow: "#F59E0B",
  red: "#EF4444",
};

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(17,24,39,0.95)",
  color: "#E5E7EB",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
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
        className={`h-64 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 flex items-center justify-center shadow-[0_10px_35px_rgba(0,0,0,0.22)] ${className ?? ""}`}
      >
        <p className="text-sm text-[#9CA3AF]">No Data Available</p>
      </div>
    );
  }

  const gradientId = `metric-grad-${kind}-${yKey}`.replace(/[^a-zA-Z0-9-_]/g, "");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`h-64 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 flex items-center justify-center shadow-[0_10px_35px_rgba(0,0,0,0.22)] ${className ?? ""}`}
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
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 4" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <Tooltip
              cursor={{ stroke: "rgba(255,255,255,0.22)", strokeDasharray: "4 4" }}
              contentStyle={chartTooltipStyle}
              labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }}
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
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 4" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <Tooltip
              cursor={{ stroke: "rgba(255,255,255,0.22)", strokeDasharray: "4 4" }}
              contentStyle={chartTooltipStyle}
              labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }}
            />
            <Line
              type="monotone"
              dataKey={yKey}
              stroke={`url(#${gradientId})`}
              strokeWidth={3}
              dot={{ r: 4, fill: CHART_COLORS.blue, stroke: "#A5B4FC", strokeWidth: 2, style: { filter: "drop-shadow(0 0 8px rgba(79,70,229,0.8))" } }}
              activeDot={{ r: 6, fill: CHART_COLORS.purple, stroke: "#C4B5FD", strokeWidth: 2 }}
              isAnimationActive
              animationDuration={750}
            />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 4" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.06)" }}
              contentStyle={chartTooltipStyle}
              labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }}
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
