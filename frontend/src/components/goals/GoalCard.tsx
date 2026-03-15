import { Goal } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ProgressRing } from "@/components/dashboard/ProgressRing";
import { Button } from "@/components/ui/button";

function statusClass(status: Goal["status"]) {
  if (status === "approved") return "bg-success/15 text-success";
  if (status === "submitted") return "bg-warning/15 text-warning";
  if (status === "rejected") return "bg-error/15 text-error";
  return "bg-muted text-muted-foreground";
}

export function GoalCard({ goal, onSubmit }: { goal: Goal; onSubmit: (id: string) => void }) {
  return (
    <Card className="space-y-4 transition hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div>
          <CardTitle>{goal.title}</CardTitle>
          <CardDescription>{goal.description || "No description"}</CardDescription>
        </div>
        <Badge className={statusClass(goal.status)}>{goal.status}</Badge>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-2">
          <Progress value={goal.progress} />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{goal.framework}</span>
            <span>{goal.weightage}% weightage</span>
          </div>
        </div>
        <ProgressRing value={goal.progress} size={64} />
      </div>

      {goal.status === "draft" && (
        <Button variant="outline" size="sm" onClick={() => onSubmit(goal.id)}>
          Submit goal
        </Button>
      )}
    </Card>
  );
}
