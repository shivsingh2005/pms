"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CalendarCheck } from "lucide-react";
import { checkinsService } from "@/services/checkins";
import { goalsService } from "@/services/goals";
import type { Checkin, Goal } from "@/types";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { formatDateTime } from "@/lib/utils";
import { useSessionStore } from "@/store/useSessionStore";
import { toast } from "sonner";

export default function CheckinsPage() {
  const [items, setItems] = useState<Checkin[]>([]);
  const [assignedGoals, setAssignedGoals] = useState<Goal[]>([]);
  const [goalId, setGoalId] = useState("");
  const [progress, setProgress] = useState(0);
  const [summary, setSummary] = useState("");
  const [blockers, setBlockers] = useState("");
  const [nextSteps, setNextSteps] = useState("");
  const [insights, setInsights] = useState<string[]>([]);
  const user = useSessionStore((s) => s.user);
  const canAccessCheckins = Boolean(user);

  const load = async () => {
    const [checkins, goals] = await Promise.all([
      checkinsService.getCheckins(),
      goalsService.getGoals(),
    ]);
    setItems(checkins);
    setAssignedGoals(goals.filter((goal) => goal.status !== "rejected"));
  };

  useEffect(() => {
    if (!canAccessCheckins) {
      return;
    }
    load().catch(() => null);
  }, [canAccessCheckins]);

  const submitCheckin = async () => {
    if (!user) {
      toast.error("Please sign in again to submit a check-in");
      return;
    }

    if (!goalId.trim()) {
      toast.error("Goal ID is required");
      return;
    }

    if (!summary.trim()) {
      toast.error("Summary is required");
      return;
    }

    try {
      const response = await checkinsService.submit({
        goal_id: goalId.trim(),
        progress,
        summary: summary.trim(),
        blockers: blockers.trim() || undefined,
        next_steps: nextSteps.trim() || undefined,
      });

      setInsights(response.insights || []);
      setGoalId("");
      setProgress(0);
      setSummary("");
      setBlockers("");
      setNextSteps("");
      toast.success("Check-in submitted");
      await load();
    } catch (error: unknown) {
      const status =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { status?: number } }).response?.status
          : undefined;

      if (status === 403) {
        toast.error("You are not allowed to submit this check-in");
        return;
      }

      toast.error("Failed to submit check-in. Please try again.");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Check-ins"
        description="Submit progress updates, wait for manager meeting approval, and track scheduled meeting details."
        action={<Button variant="outline" onClick={() => load().catch(() => null)}>Refresh</Button>}
      />

      <SectionContainer columns="dashboard">
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <CalendarCheck className="h-3.5 w-3.5" /> My Check-ins
          </div>
          <CardTitle>Submit Check-in</CardTitle>
          <CardDescription>{"Lifecycle: draft -> submitted -> reviewed"}</CardDescription>
          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Assigned Goal</label>
              <select
                className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground"
                value={goalId}
                onChange={(event) => setGoalId(event.target.value)}
              >
                <option value="">Select a goal</option>
                {assignedGoals.map((goal) => (
                  <option key={goal.id} value={goal.id}>
                    {goal.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Progress: {progress}%</label>
              <input
                type="range"
                min={0}
                max={100}
                step={1}
                value={progress}
                onChange={(event) => setProgress(Number(event.target.value))}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Summary</label>
              <Textarea value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="What did you complete since last update?" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Blockers</label>
              <Textarea value={blockers} onChange={(e) => setBlockers(e.target.value)} placeholder="Any blockers currently impacting delivery" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Next Steps</label>
              <Textarea value={nextSteps} onChange={(e) => setNextSteps(e.target.value)} placeholder="What will you do next?" />
            </div>
          </div>
          <Button onClick={submitCheckin}>Submit Check-in</Button>
          {insights.length > 0 && (
            <div className="rounded-lg border border-border/70 p-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Insights</p>
              <ul className="mt-2 space-y-1 text-sm text-foreground">
                {insights.map((line, idx) => (
                  <li key={`${line}-${idx}`}>{line}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>

        <div className="space-y-6 xl:col-span-8">
          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Submitted Check-ins</CardTitle>
            <div className="mt-4">
              <DataTable
                rows={items}
                rowKey={(row) => row.id}
                emptyState="No check-ins submitted yet"
                columns={[
                  {
                    key: "status",
                    header: "Status",
                    render: (row) => (
                      <Badge
                        className={
                          row.status === "reviewed"
                            ? "bg-success/15 text-success"
                            : row.status === "submitted"
                              ? "bg-warning/15 text-warning"
                              : "bg-muted text-muted-foreground"
                        }
                      >
                        {row.status}
                      </Badge>
                    ),
                  },
                  {
                    key: "goal_id",
                    header: "Goal",
                    render: (row) => assignedGoals.find((goal) => goal.id === row.goal_id)?.title || row.goal_id,
                  },
                  {
                    key: "progress",
                    header: "Progress",
                    render: (row) => `${row.progress}%`,
                  },
                  {
                    key: "summary",
                    header: "Summary",
                    render: (row) => row.summary || "-",
                  },
                  {
                    key: "manager_feedback",
                    header: "Manager Feedback",
                    render: (row) => row.manager_feedback || "Pending review",
                  },
                  {
                    key: "meeting_date",
                    header: "Meeting",
                    render: (row) => (row.meeting_date ? formatDateTime(row.meeting_date) : "Awaiting manager approval"),
                  },
                  {
                    key: "meeting_link",
                    header: "Meet Link",
                    render: (row) => {
                      if (!row.meeting_link) return "Pending scheduling";
                      return (
                        <a
                          href={row.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          className="text-primary underline-offset-2 hover:underline"
                        >
                          Open Meet
                        </a>
                      );
                    },
                  },
                  {
                    key: "created_at",
                    header: "Created",
                    render: (row) => formatDateTime(row.created_at),
                  },
                ]}
              />
            </div>
          </Card>
        </div>
      </SectionContainer>
    </motion.div>
  );
}
