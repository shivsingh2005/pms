"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

interface PieChartWrapperProps {
  data: Array<{ name: string; value: number; color?: string; [key: string]: string | number | undefined }>;
  dataKey?: string;
  nameKey?: string;
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
  colors?: string[];
  tooltipStyle?: Record<string, string | number>;
}

export default function PieChartWrapper({
  data,
  dataKey = "value",
  nameKey = "name",
  height = 224,
  innerRadius = 55,
  outerRadius = 86,
  colors,
  tooltipStyle,
}: PieChartWrapperProps) {
  if (!data || data.length === 0) {
    return <div className="flex h-full items-center justify-center text-sm text-muted-foreground">No data available</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={height} minWidth={0} minHeight={0}>
      <PieChart>
        <Pie data={data} dataKey={dataKey} nameKey={nameKey} innerRadius={innerRadius} outerRadius={outerRadius} paddingAngle={3}>
          {data.map((entry, index) => {
            const entryColor = typeof entry.color === "string" ? entry.color : undefined;
            const paletteColor = colors?.[index % (colors.length || 1)];
            return <Cell key={`${String(entry[nameKey])}-${index}`} fill={entryColor || paletteColor || "hsl(var(--primary))"} />;
          })}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
      </PieChart>
    </ResponsiveContainer>
  );
}
