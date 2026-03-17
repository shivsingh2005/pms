import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ProgressRing } from "@/components/dashboard/ProgressRing";
import { CardTitle } from "@/components/ui/card";

interface ProgressCardProps {
  title: string;
  value: number;
  className?: string;
}

export function ProgressCard({ title, value, className }: ProgressCardProps) {
  return (
    <DashboardCard className={className}>
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <CardTitle className="text-center">{title}</CardTitle>
        <ProgressRing value={value} size={128} />
      </div>
    </DashboardCard>
  );
}
