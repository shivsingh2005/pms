import type { ReactNode } from "react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { CardDescription, CardTitle } from "@/components/ui/card";

interface ChartCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export function ChartCard({ title, description, children, className }: ChartCardProps) {
  return (
    <DashboardCard className={className}>
      <CardTitle>{title}</CardTitle>
      {description ? <CardDescription className="mt-1">{description}</CardDescription> : null}
      <div className="mt-4">{children}</div>
    </DashboardCard>
  );
}
