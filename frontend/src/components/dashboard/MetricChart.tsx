"use client";

import { motion } from "framer-motion";
import { MetricChartCanvas } from "@/components/charts/MetricChartCanvas";

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
      <MetricChartCanvas
        kind={kind}
        data={data}
        xKey={xKey}
        yKey={yKey}
        color={color}
        barPalette={barPalette}
        chartTooltipStyle={chartTooltipStyle}
        gradientId={gradientId}
      />
    </motion.div>
  );
}

