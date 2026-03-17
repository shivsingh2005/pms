"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
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
}

export function MetricChart({ kind, data, xKey, yKey, color = "hsl(var(--primary))", className }: MetricChartProps) {
  return (
    <div className={`h-64 rounded-2xl border border-border/80 bg-surface/55 p-4 flex items-center justify-center ${className ?? ""}`}>
      <ResponsiveContainer width="100%" height="100%">
        {kind === "area" ? (
          <AreaChart data={data}>
            <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="4 5" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <Tooltip
              cursor={{ stroke: "hsl(var(--border))", strokeDasharray: "4 4" }}
              contentStyle={{
                borderRadius: 14,
                borderColor: "hsl(var(--border))",
                backgroundColor: "hsl(var(--card))",
                boxShadow: "var(--shadow-sm)",
              }}
            />
            <Area type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} fill="hsl(var(--primary) / 0.16)" />
          </AreaChart>
        ) : kind === "line" ? (
          <LineChart data={data}>
            <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="4 5" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <Tooltip
              cursor={{ stroke: "hsl(var(--border))", strokeDasharray: "4 4" }}
              contentStyle={{
                borderRadius: 14,
                borderColor: "hsl(var(--border))",
                backgroundColor: "hsl(var(--card))",
                boxShadow: "var(--shadow-sm)",
              }}
            />
            <Line
              type="monotone"
              dataKey={yKey}
              stroke={color}
              strokeWidth={2.5}
              dot={{ r: 3, fill: color }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="4 5" />
            <XAxis dataKey={xKey} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: "hsl(var(--muted) / 0.5)" }}
              contentStyle={{
                borderRadius: 14,
                borderColor: "hsl(var(--border))",
                backgroundColor: "hsl(var(--card))",
                boxShadow: "var(--shadow-sm)",
              }}
            />
            <Bar dataKey={yKey} fill={color} radius={[8, 8, 3, 3]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
