import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ProgressRing } from "@/components/dashboard/ProgressRing";

interface ProgressWidgetProps {
  progress: number;
  framework: string;
  weightage: number;
}

function progressMeta(progress: number) {
  if (progress >= 70) return { label: "On Track", className: "border-success/25 bg-success/12 text-success" };
  if (progress >= 40) return { label: "At Risk", className: "border-warning/25 bg-warning/12 text-warning" };
  return { label: "Behind", className: "border-error/25 bg-error/12 text-error" };
}

export function ProgressWidget({ progress, framework, weightage }: ProgressWidgetProps) {
  const status = progressMeta(progress);

  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0 flex-1 space-y-2">
        <Progress value={progress} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{framework}</span>
          <span>{weightage}% weightage</span>
        </div>
        <Badge className={status.className}>{status.label}</Badge>
      </div>
      <ProgressRing value={progress} size={64} />
    </div>
  );
}
