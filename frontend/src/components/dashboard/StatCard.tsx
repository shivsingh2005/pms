import type { ComponentType } from "react";
import { MetricCard } from "@/components/dashboard/MetricCard";

interface StatCardProps {
  title: string;
  value: string;
  trendLabel: string;
  trend?: "up" | "down" | "flat";
  icon: ComponentType<{ className?: string }>;
  className?: string;
}

export function StatCard({ title, value, trendLabel, trend = "flat", icon: Icon, className }: StatCardProps) {
  return (
    <MetricCard
      title={title}
      value={value}
      trendLabel={trendLabel}
      trend={trend}
      icon={Icon}
      className={className}
    />
  );
}
