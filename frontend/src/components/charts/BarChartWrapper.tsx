"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type DataPoint = Record<string, number | string | null | undefined>;

export default function BarChartWrapper({
  data,
  xKey,
  yKey,
  color = "hsl(var(--primary))",
  height = 280,
}: {
  data: DataPoint[];
  xKey: string;
  yKey: string;
  color?: string;
  height?: number;
}) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={yKey} fill={color} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
