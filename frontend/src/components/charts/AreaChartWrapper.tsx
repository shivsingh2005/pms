"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type DataPoint = Record<string, number | string | null | undefined>;

export default function AreaChartWrapper({
  data,
  xKey,
  yKey,
  color = "hsl(var(--primary))",
  height = 300,
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
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey={yKey} stroke={color} fill={color} fillOpacity={0.2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
