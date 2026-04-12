"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { goalsService } from "@/services/goals";
import { useSessionStore } from "@/store/useSessionStore";
import type { ManagerPendingGoal } from "@/types";

export default function ManagerGoalApprovalsPage() {
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);

  const [pendingGoals, setPendingGoals] = useState<ManagerPendingGoal[]>([]);
  const [goalCommentById, setGoalCommentById] = useState<Record<string, string>>({});
  const [savingGoalId, setSavingGoalId] = useState<string | null>(null);

  const load = async () => {
    const pending = await goalsService.getManagerPendingGoals();
    setPendingGoals(pending);
  };

  useEffect(() => {
    if (!user) {
      return;
    }
    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, setActiveMode, user]);

  useEffect(() => {
    if (!user || activeMode !== "manager") {
      return;
    }
    load().catch(() => {
      toast.error("Failed to load goal approvals");
    });
  }, [activeMode, user]);

  const decideGoal = async (goalId: string, action: "approve" | "request-edit" | "reject") => {
    const comment = (goalCommentById[goalId] || "").trim();

    if (action === "reject" && !comment) {
      toast.error("Rejection reason is required");
      return;
    }

    setSavingGoalId(goalId);
    try {
      if (action === "approve") {
        await goalsService.managerApproveGoal(goalId, comment || undefined);
      } else if (action === "request-edit") {
        await goalsService.managerRequestEdit(goalId, comment || undefined);
      } else {
        await goalsService.managerRejectGoal(goalId, comment);
      }

      setGoalCommentById((prev) => ({ ...prev, [goalId]: "" }));
      await load();
      toast.success("Goal decision saved");
    } catch {
      toast.error("Failed to save goal decision");
    } finally {
      setSavingGoalId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goal Approvals"
        description="Approve, request edits, or reject self-created employee goals before check-ins can be submitted."
        action={
          <Button variant="outline" onClick={() => load().catch(() => toast.error("Refresh failed"))}>
            Refresh
          </Button>
        }
      />

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Pending Self-Created Goals</CardTitle>
        <CardDescription>Employees can proceed to check-ins only after these goals are approved.</CardDescription>

        {pendingGoals.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending goals awaiting approval.</p>
        ) : (
          pendingGoals.map((item) => (
            <div key={item.goal.id} className="space-y-2 rounded-md border border-border/70 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{item.goal.title}</p>
                <p className="text-xs text-muted-foreground">{item.goal.weightage}%</p>
              </div>
              <p className="text-xs text-muted-foreground">
                {item.employee_name} ({item.employee_role})
              </p>
              {item.goal.description ? <p className="text-xs text-muted-foreground">{item.goal.description}</p> : null}

              <Textarea
                placeholder="Manager comment (required for reject)"
                value={goalCommentById[item.goal.id] || ""}
                onChange={(event) => setGoalCommentById((prev) => ({ ...prev, [item.goal.id]: event.target.value }))}
              />

              <div className="flex flex-wrap gap-2">
                <Button size="sm" onClick={() => decideGoal(item.goal.id, "approve")} disabled={savingGoalId === item.goal.id}>
                  Approve
                </Button>
                <Button size="sm" variant="secondary" onClick={() => decideGoal(item.goal.id, "request-edit")} disabled={savingGoalId === item.goal.id}>
                  Request Edit
                </Button>
                <Button size="sm" variant="outline" onClick={() => decideGoal(item.goal.id, "reject")} disabled={savingGoalId === item.goal.id}>
                  Reject
                </Button>
              </div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}