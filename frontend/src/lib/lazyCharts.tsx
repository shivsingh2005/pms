"use client";

import dynamic from "next/dynamic";
import { ChartSkeleton } from "@/components/ui/skeletons";

export const LazyMetricChartCanvas = dynamic(
  () => import("@/components/charts/MetricChartCanvas").then((mod) => mod.MetricChartCanvas),
  {
    ssr: false,
    loading: () => <ChartSkeleton height={256} />,
  },
);

export const LazyPieChart = dynamic(() => import("@/components/charts/PieChartWrapper"), {
  ssr: false,
  loading: () => <ChartSkeleton height={224} />,
});
