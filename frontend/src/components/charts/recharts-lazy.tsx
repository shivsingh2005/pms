"use client";

import dynamic from "next/dynamic";

function ChartSkeleton() {
  return <div className="h-64 w-full animate-pulse rounded-xl bg-muted" />;
}

const lazy = <T,>(loader: () => Promise<T>) =>
  dynamic(loader as never, {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }) as unknown as T;

export const ResponsiveContainer = lazy(() => import("recharts").then((mod) => mod.ResponsiveContainer));
export const CartesianGrid = lazy(() => import("recharts").then((mod) => mod.CartesianGrid));
export const Tooltip = lazy(() => import("recharts").then((mod) => mod.Tooltip));
export const XAxis = lazy(() => import("recharts").then((mod) => mod.XAxis));
export const YAxis = lazy(() => import("recharts").then((mod) => mod.YAxis));
export const LineChart = lazy(() => import("recharts").then((mod) => mod.LineChart));
export const Line = lazy(() => import("recharts").then((mod) => mod.Line));
export const AreaChart = lazy(() => import("recharts").then((mod) => mod.AreaChart));
export const Area = lazy(() => import("recharts").then((mod) => mod.Area));
export const BarChart = lazy(() => import("recharts").then((mod) => mod.BarChart));
export const Bar = lazy(() => import("recharts").then((mod) => mod.Bar));
export const PieChart = lazy(() => import("recharts").then((mod) => mod.PieChart));
export const Pie = lazy(() => import("recharts").then((mod) => mod.Pie));
export const Cell = lazy(() => import("recharts").then((mod) => mod.Cell));
