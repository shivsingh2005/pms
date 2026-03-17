import type { ComponentType } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { CardDescription, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  trendLabel: string;
  trend?: "up" | "down" | "flat";
  icon: ComponentType<{ className?: string }>;
  className?: string;
}

export function MetricCard({ title, value, trendLabel, trend = "flat", icon: Icon, className }: MetricCardProps) {
  const trendClass = trend === "up" ? "text-success" : trend === "down" ? "text-error" : "text-muted-foreground";
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;

  return (
    <DashboardCard className={cn("h-28 p-5", className)}>
      <div className="flex h-full flex-col justify-between">
      <div className="flex items-start justify-between gap-3">
        <div>
          <CardDescription className="text-sm">{title}</CardDescription>
          <CardTitle className="mt-2 text-3xl font-semibold">{value}</CardTitle>
        </div>
        <span className="rounded-xl border border-border/80 bg-surface p-2.5 text-primary">
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className={cn("inline-flex items-center gap-1 text-xs font-medium", trendClass)}>
        <TrendIcon className="h-3.5 w-3.5" />
        {trendLabel}
      </div>
      </div>
    </DashboardCard>
  );
}
