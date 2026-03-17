import { Goal } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { ProgressWidget } from "@/components/dashboard/ProgressWidget";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

function statusClass(status: Goal["status"]) {
  if (status === "approved") return "border-success/25 bg-success/15 text-success";
  if (status === "submitted") return "border-warning/25 bg-warning/15 text-warning";
  if (status === "rejected") return "border-error/25 bg-error/15 text-error";
  return "border-border/70 bg-muted text-muted-foreground";
}

export function GoalCard({ goal, onSubmit }: { goal: Goal; onSubmit: (id: string) => void }) {
  const copyGoalId = async () => {
    try {
      await navigator.clipboard.writeText(goal.id);
      toast.success("Goal ID copied");
    } catch {
      toast.error("Unable to copy Goal ID");
    }
  };

  return (
    <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 transition hover:-translate-y-0.5 hover:shadow-elevated">
      <div className="flex items-start justify-between">
        <div>
          <CardTitle>{goal.title}</CardTitle>
          <CardDescription>{goal.description || "No description"}</CardDescription>
          <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-medium">Goal ID:</span>
            <code className="rounded bg-muted px-1.5 py-0.5 text-[11px]">{goal.id}</code>
            <button
              type="button"
              className="text-primary hover:underline"
              onClick={copyGoalId}
            >
              Copy
            </button>
          </div>
        </div>
        <Badge className={statusClass(goal.status)}>{goal.status}</Badge>
      </div>

      <ProgressWidget progress={goal.progress} framework={goal.framework} weightage={goal.weightage} />

      {goal.status === "draft" && (
        <Button variant="outline" size="sm" onClick={() => onSubmit(goal.id)}>
          Submit goal
        </Button>
      )}
    </Card>
  );
}
