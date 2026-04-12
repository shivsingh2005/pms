'use client';

import dynamic from 'next/dynamic';

const skeleton = (h: number) => function ChartLoading() {
  return (
    <div
      className="w-full animate-pulse rounded-lg bg-muted"
      style={{ height: h }}
    />
  );
};

export const LazyLineChart = dynamic(
  () => import('./LineChartWrapper'),
  { ssr: false, loading: skeleton(300) }
);

export const LazyBarChart = dynamic(
  () => import('./BarChartWrapper'),
  { ssr: false, loading: skeleton(280) }
);

export const LazyPieChart = dynamic(
  () => import('./PieChartWrapper'),
  { ssr: false, loading: skeleton(280) }
);

export const LazyAreaChart = dynamic(
  () => import('./AreaChartWrapper'),
  { ssr: false, loading: skeleton(300) }
);

export const LazyMetricChartCanvas = dynamic(
  () => import('./MetricChartCanvas').then((mod) => mod.MetricChartCanvas),
  { ssr: false, loading: skeleton(300) }
);
