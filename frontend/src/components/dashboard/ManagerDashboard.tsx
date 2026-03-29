"use client";

import { useEffect, useState } from "react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { dashboardService, type DashboardOverview } from "@/services/dashboard";
import { managerService } from "@/services/manager";
import { checkinsService } from "@/services/checkins";
import { goalsService } from "@/services/goals";
import type { ManagerTeamMember } from "@/types";
import type { ManagerPendingCheckin } from "@/types";
import type { Goal } from "@/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useSessionStore } from "@/store/useSessionStore";

export function ManagerDashboard() {
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [team, setTeam] = useState<ManagerTeamMember[]>([]);
  const [pendingCheckins, setPendingCheckins] = useState<ManagerPendingCheckin[]>([]);
  const [pendingGoals, setPendingGoals] = useState<Goal[]>([]);
  const [pendingProposalsCount, setPendingProposalsCount] = useState(0);
  const [feedbackByCheckin, setFeedbackByCheckin] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user || activeMode !== "manager") {
      setOverview(null);
      setTeam([]);
      setPendingCheckins([]);
      setPendingGoals([]);
      setPendingProposalsCount(0);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.allSettled([
      dashboardService.getOverview(),
      managerService.getTeam(),
      managerService.getPendingCheckins(),
      goalsService.getGoals(),
      managerService.getPendingMeetingProposals(),
    ])
      .then(([overviewResult, teamResult, pendingCheckinsResult, goalsResult, proposalsResult]) => {
        if (cancelled) {
          return;
        }

        if (overviewResult.status === "fulfilled") {
          setOverview(overviewResult.value);
        } else {
          setOverview(null);
        }

        if (teamResult.status === "fulfilled") {
          setTeam(teamResult.value);
        } else {
          setTeam([]);
        }

        if (pendingCheckinsResult.status === "fulfilled") {
          setPendingCheckins(pendingCheckinsResult.value);
        } else {
          setPendingCheckins([]);
        }

        if (goalsResult.status === "fulfilled") {
          setPendingGoals(goalsResult.value.filter((goal) => goal.status === "submitted"));
        } else {
          setPendingGoals([]);
        }

        if (proposalsResult.status === "fulfilled") {
          setPendingProposalsCount(proposalsResult.value.length);
        } else {
          setPendingProposalsCount(0);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeMode, user]);

  const reviewCheckin = async (checkinId: string) => {
    const feedback = feedbackByCheckin[checkinId]?.trim();
    if (!feedback) {
      toast.error("Manager feedback is required");
      return;
    }

    try {
      await checkinsService.review(checkinId, { manager_feedback: feedback, status: "reviewed" });
      setPendingCheckins((prev) => prev.filter((item) => item.id !== checkinId));
      setFeedbackByCheckin((prev) => ({ ...prev, [checkinId]: "" }));
      toast.success("Check-in reviewed");
    } catch {
      toast.error("Failed to review check-in");
    }
  };

  const decideGoal = async (goalId: string, action: "approve" | "reject") => {
    try {
      if (action === "approve") {
        await goalsService.approveGoal(goalId);
      } else {
        await goalsService.rejectGoal(goalId);
      }
      setPendingGoals((prev) => prev.filter((goal) => goal.id !== goalId));
      toast.success(action === "approve" ? "Goal approved" : "Goal rejected");
    } catch {
      toast.error(`Failed to ${action} goal`);
    }
  };

  const pendingApprovalsCount = pendingCheckins.length + pendingGoals.length + pendingProposalsCount;

  if (activeMode !== "manager") {
    return (
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Manager mode required</CardTitle>
        <CardDescription>Switch to Manager Mode to load team data and approvals.</CardDescription>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Team Overview</CardTitle>
        <CardDescription>{loading ? "Loading..." : `${overview?.kpi.active_reports ?? team.length} active reports.`}</CardDescription>
      </Card>
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Goal Allotment</CardTitle>
        <CardDescription>{loading ? "Loading..." : `${overview?.kpi.team_goals ?? 0} team goals currently tracked.`}</CardDescription>
      </Card>
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Pending Approvals</CardTitle>
        <CardDescription>
          {loading
            ? "Loading..."
            : `${pendingApprovalsCount} pending total (${pendingGoals.length} goals, ${pendingCheckins.length} check-ins, ${pendingProposalsCount} meetings).`}
        </CardDescription>
      </Card>
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Team Performance</CardTitle>
        <CardDescription>{loading ? "Loading..." : `Team consistency: ${overview?.kpi.consistency ?? 0}%.`}</CardDescription>
      </Card>
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Meetings</CardTitle>
        <CardDescription>Coordinate weekly check-ins and escalation meetings for your team.</CardDescription>
      </Card>
      <Card className="space-y-2 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>AI Insights</CardTitle>
        <CardDescription>{overview?.insights.primary || "AI team insights unavailable."}</CardDescription>
      </Card>

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 lg:col-span-2">
        <CardTitle>Pending Goal Approvals</CardTitle>
        <CardDescription>Submitted goals awaiting your decision.</CardDescription>

        {pendingGoals.length === 0 ? (
          <p className="text-sm text-muted-foreground">No submitted goals waiting for approval.</p>
        ) : (
          pendingGoals.map((goal) => {
            const ownerName = team.find((member) => member.id === goal.user_id)?.name || "Team member";
            return (
              <div key={goal.id} className="space-y-2 rounded-md border border-border/70 p-3">
                <p className="text-sm font-medium text-foreground">{goal.title}</p>
                <p className="text-xs text-muted-foreground">Owner: {ownerName} | Progress: {goal.progress}% | Weightage: {goal.weightage}%</p>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => decideGoal(goal.id, "approve")}>Approve</Button>
                  <Button size="sm" variant="outline" onClick={() => decideGoal(goal.id, "reject")}>Reject</Button>
                </div>
              </div>
            );
          })
        )}
      </Card>

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 lg:col-span-2">
        <CardTitle>Pending Check-ins</CardTitle>
        <CardDescription>Submitted check-ins awaiting manager review.</CardDescription>

        {pendingCheckins.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending check-ins.</p>
        ) : (
          pendingCheckins.map((item) => (
            <div key={item.id} className="space-y-2 rounded-md border border-border/70 p-3">
              <p className="text-sm font-medium text-foreground">{item.employee_name} · {item.goal_title}</p>
              <p className="text-xs text-muted-foreground">Progress: {item.progress}%</p>
              {item.blockers ? <p className="text-sm text-muted-foreground">Blockers: {item.blockers}</p> : null}
              <Textarea
                value={feedbackByCheckin[item.id] || ""}
                onChange={(event) => setFeedbackByCheckin((prev) => ({ ...prev, [item.id]: event.target.value }))}
                placeholder="Add manager feedback"
              />
              <Button size="sm" onClick={() => reviewCheckin(item.id)}>Review</Button>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
