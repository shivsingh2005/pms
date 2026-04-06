"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Users } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { GoalLineageGraph } from "@/components/goals/GoalLineageGraph";
import { goalsService } from "@/services/goals";
import { managerService } from "@/services/manager";
import { useSessionStore } from "@/store/useSessionStore";
import type {
  Goal,
  GoalAssignmentCandidate,
  GoalChangeLog,
  GoalDriftInsight,
  GoalLineage,
  ManagerTeamMember,
  RoleGoalCluster,
  RoleGoalRecommendation,
} from "@/types";

type RoleKey = "frontend" | "backend" | "others";

interface GoalEditorState {
  role: RoleKey;
  title: string;
  description: string;
  kpi: string;
  weightage: number;
}

interface CascadeTargetState {
  employee_id: string;
  employee_name: string;
  selected: boolean;
  contribution_weight: number;
}

function workloadColor(workload: number): string {
  if (workload < 50) return "bg-emerald-500";
  if (workload < 80) return "bg-amber-500";
  return "bg-red-500";
}

function workloadBadgeClass(status: "low" | "medium" | "high"): string {
  if (status === "low") return "bg-emerald-500/15 text-emerald-600";
  if (status === "medium") return "bg-amber-500/15 text-amber-700";
  return "bg-red-500/15 text-red-600";
}

function roleLabel(role: RoleKey): string {
  if (role === "frontend") return "Frontend";
  if (role === "backend") return "Backend";
  return "Others";
}

export default function ManagerGoalsAllotmentPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const setActiveMode = useSessionStore((s) => s.setActiveMode);

  const [objective, setObjective] = useState("");
  const [generating, setGenerating] = useState(false);
  const [clusters, setClusters] = useState<RoleGoalCluster[]>([]);
  const [activeRole, setActiveRole] = useState<RoleKey>("frontend");

  const [assignOpen, setAssignOpen] = useState(false);
  const [editor, setEditor] = useState<GoalEditorState | null>(null);
  const [candidates, setCandidates] = useState<GoalAssignmentCandidate[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [allowOverload, setAllowOverload] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const [managerGoals, setManagerGoals] = useState<Goal[]>([]);
  const [teamMembers, setTeamMembers] = useState<ManagerTeamMember[]>([]);
  const [parentGoalId, setParentGoalId] = useState("");
  const [cascadeTargets, setCascadeTargets] = useState<CascadeTargetState[]>([]);
  const [cascading, setCascading] = useState(false);

  const [drifts, setDrifts] = useState<GoalDriftInsight[]>([]);
  const [lineageGoalId, setLineageGoalId] = useState("");
  const [lineage, setLineage] = useState<GoalLineage | null>(null);
  const [changeLogs, setChangeLogs] = useState<GoalChangeLog[]>([]);

  const initializePhase2 = useCallback(async () => {
    try {
      const [goals, members, driftRows] = await Promise.all([
        goalsService.getGoals(),
        managerService.getTeam({ silent: true }),
        goalsService.getGoalDriftInsights(),
      ]);

      const ownGoals = goals.filter((goal) => goal.user_id === user?.id);
      setManagerGoals(ownGoals);
      if (ownGoals.length > 0) {
        setParentGoalId(ownGoals[0].id);
      }

      setTeamMembers(members);
      setCascadeTargets(
        members.map((member) => ({
          employee_id: member.id,
          employee_name: member.name,
          selected: false,
          contribution_weight: 25,
        })),
      );

      setDrifts(driftRows);
    } catch {
      toast.error("Unable to load Phase 2 goal data");
    }
  }, [user?.id]);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (user.role !== "manager") {
      router.push("/unauthorized");
      return;
    }

    if (activeMode !== "manager") {
      setActiveMode("manager");
    }

    void initializePhase2();
  }, [activeMode, initializePhase2, router, setActiveMode, user]);

  const clusterMap = useMemo(() => {
    const map: Record<RoleKey, RoleGoalRecommendation[]> = {
      frontend: [],
      backend: [],
      others: [],
    };

    for (const cluster of clusters) {
      const key = (cluster.role || "others") as RoleKey;
      if (key in map) {
        map[key] = cluster.goals || [];
      }
    }

    return map;
  }, [clusters]);

  const visibleGoals = clusterMap[activeRole] || [];

  const generateRoleClusters = async () => {
    setGenerating(true);
    try {
      const payload = await goalsService.getAssignmentRecommendations({
        organization_objectives: objective.trim() || undefined,
      });
      setClusters(payload.clusters || []);
      toast.success("Role-based AI goal clusters generated");
    } catch (error: unknown) {
      const message =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      toast.error(message || "Failed to generate role-based goal clusters");
    } finally {
      setGenerating(false);
    }
  };

  const openAssignModal = async (role: RoleKey, goal: RoleGoalRecommendation) => {
    setEditor({
      role,
      title: goal.title,
      description: goal.description,
      kpi: goal.kpi || "",
      weightage: goal.suggested_weight,
    });
    setAssignOpen(true);
    setSelectedEmployeeId("");
    setAllowOverload(false);

    setLoadingCandidates(true);
    try {
      const rows = await goalsService.getAssignmentCandidates(role);
      setCandidates(rows);
    } catch {
      setCandidates([]);
      toast.error("Failed to load role-matched employees");
    } finally {
      setLoadingCandidates(false);
    }
  };

  const submitAssignment = async () => {
    if (!editor) return;

    if (!selectedEmployeeId) {
      toast.error("Select an employee");
      return;
    }

    if (!editor.title.trim() || !editor.description.trim()) {
      toast.error("Goal title and description are required");
      return;
    }

    if (editor.weightage <= 0 || editor.weightage > 100) {
      toast.error("Weightage must be between 1 and 100");
      return;
    }

    setAssigning(true);
    try {
      const result = await goalsService.assignSingleGoal({
        employee_id: selectedEmployeeId,
        role: editor.role,
        title: editor.title.trim(),
        description: editor.description.trim(),
        kpi: editor.kpi.trim() || undefined,
        weightage: editor.weightage,
        framework: "OKR",
        progress: 0,
        approve: true,
        allow_overload: allowOverload,
        is_ai_generated: true,
      });

      if (result.warning) {
        toast.warning(`Assigned with warning: ${result.warning}`);
      } else {
        toast.success("Goal assigned successfully");
      }

      const refreshed = await goalsService.getAssignmentCandidates(editor.role);
      setCandidates(refreshed);
      setAssignOpen(false);
      setEditor(null);
      setSelectedEmployeeId("");
    } catch (error: unknown) {
      const message =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      toast.error(message || "Failed to assign goal");
    } finally {
      setAssigning(false);
    }
  };

  const submitCascade = async () => {
    if (!editor) {
      toast.error("Select a goal template first from role clusters");
      return;
    }
    if (!parentGoalId) {
      toast.error("Select a parent goal");
      return;
    }

    const selectedTargets = cascadeTargets.filter((row) => row.selected);
    if (selectedTargets.length === 0) {
      toast.error("Select at least one team member for cascade");
      return;
    }

    setCascading(true);
    try {
      const result = await goalsService.cascadeGoal({
        parent_goal_id: parentGoalId,
        normalize_weights: true,
        children: selectedTargets.map((row) => ({
          employee_id: row.employee_id,
          title: editor.title,
          description: editor.description,
          kpi: editor.kpi || undefined,
          framework: "OKR",
          weightage: row.contribution_weight,
          progress: 0,
        })),
      });

      toast.success(`Cascaded to ${result.children_created} team members`);
      const driftRows = await goalsService.getGoalDriftInsights();
      setDrifts(driftRows);
    } catch {
      toast.error("Failed to cascade goal");
    } finally {
      setCascading(false);
    }
  };

  const loadLineage = async () => {
    if (!lineageGoalId.trim()) {
      toast.error("Enter a goal ID");
      return;
    }

    try {
      const [graph, logs] = await Promise.all([
        goalsService.getGoalLineage(lineageGoalId.trim()),
        goalsService.getGoalChanges(lineageGoalId.trim()),
      ]);
      setLineage(graph);
      setChangeLogs(logs);
    } catch {
      toast.error("Unable to fetch lineage for this goal");
    }
  };

  if (!user || user.role !== "manager") {
    return null;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Manager Goal Assignment"
        description="AI suggests role-based goals; managers manually assign with role match and workload checks."
        action={
          <Button onClick={generateRoleClusters} disabled={generating}>
            <Sparkles className="mr-2 h-4 w-4" />
            {generating ? "Generating..." : "Generate Role Clusters"}
          </Button>
        }
      />

      <Card className="rounded-xl border bg-card p-5 space-y-3">
        <CardTitle>AI Context</CardTitle>
        <CardDescription>Provide optional objectives to improve AI role clustering quality.</CardDescription>
        <Textarea
          value={objective}
          onChange={(event) => setObjective(event.target.value)}
          placeholder="Example: Improve frontend UX speed and backend API reliability this quarter."
        />
      </Card>

      <Card className="rounded-xl border bg-card p-5 space-y-4">
        <CardTitle>Goal Clusters</CardTitle>
        <div className="flex flex-wrap gap-2">
          {(["frontend", "backend", "others"] as RoleKey[]).map((role) => (
            <Button
              key={role}
              variant={activeRole === role ? "default" : "outline"}
              onClick={() => setActiveRole(role)}
            >
              {roleLabel(role)}
            </Button>
          ))}
        </div>

        {visibleGoals.length === 0 ? (
          <p className="text-sm text-muted-foreground">No goals available for {roleLabel(activeRole)}. Generate clusters to continue.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {visibleGoals.map((goal, index) => (
              <div key={`${activeRole}-${index}`} className="rounded-lg border border-border/70 p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-foreground">{goal.title}</p>
                  <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs text-primary">{goal.difficulty}</span>
                </div>
                <p className="text-sm text-muted-foreground">{goal.description}</p>
                {goal.kpi ? <p className="text-xs text-muted-foreground">KPI: {goal.kpi}</p> : null}
                <p className="text-xs text-muted-foreground">Suggested weight: {goal.suggested_weight}%</p>
                <Button size="sm" onClick={() => openAssignModal(activeRole, goal)}>Assign</Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="rounded-xl border bg-card p-5 space-y-4">
        <CardTitle>Cascade and Contribution Allocation</CardTitle>
        <CardDescription>
          Create child goals from a selected parent goal. Contribution percentages are normalized to 100%.
        </CardDescription>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Parent Goal</p>
            <select
              className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
              value={parentGoalId}
              onChange={(event) => setParentGoalId(event.target.value)}
            >
              {managerGoals.length === 0 ? (
                <option value="">No manager goals available</option>
              ) : (
                managerGoals.map((goal) => (
                  <option key={goal.id} value={goal.id}>{goal.title}</option>
                ))
              )}
            </select>
          </div>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Goal Template Source</p>
            <p className="text-sm text-foreground">
              {editor ? `${editor.title} (${roleLabel(editor.role)})` : "Pick an AI cluster goal and click Assign to seed cascade content."}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {teamMembers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No direct reports found.</p>
          ) : (
            cascadeTargets.map((row, index) => (
              <div key={row.employee_id} className="rounded-lg border border-border/70 p-3">
                <div className="grid grid-cols-1 gap-2 md:grid-cols-[auto_1fr_180px] md:items-center">
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={row.selected}
                      onChange={(event) => {
                        const checked = event.target.checked;
                        setCascadeTargets((prev) => prev.map((item, idx) => idx === index ? { ...item, selected: checked } : item));
                      }}
                    />
                    Cascade
                  </label>
                  <p className="text-sm text-foreground">{row.employee_name}</p>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    value={row.contribution_weight}
                    onChange={(event) => {
                      const next = Number(event.target.value || 0);
                      setCascadeTargets((prev) => prev.map((item, idx) => idx === index ? { ...item, contribution_weight: next } : item));
                    }}
                    placeholder="Contribution"
                  />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end">
          <Button onClick={submitCascade} disabled={cascading || !editor}>
            {cascading ? "Cascading..." : "Cascade Goal"}
          </Button>
        </div>
      </Card>

      <Card className="rounded-xl border bg-card p-5 space-y-4">
        <CardTitle>Lineage and Drift</CardTitle>
        <CardDescription>Inspect goal lineage graph and identify drift-risk goals.</CardDescription>

        <div className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_auto]">
          <Input value={lineageGoalId} onChange={(event) => setLineageGoalId(event.target.value)} placeholder="Enter goal ID" />
          <Button variant="outline" onClick={loadLineage}>Load Lineage</Button>
        </div>

        {lineage ? (
          <GoalLineageGraph lineage={lineage} />
        ) : null}

        <div className="rounded-lg border border-border/70 p-3 space-y-2">
          <p className="text-sm font-medium text-foreground">Recent Goal Change Log</p>
          {changeLogs.length === 0 ? (
            <p className="text-xs text-muted-foreground">No change history loaded.</p>
          ) : (
            changeLogs.slice(0, 6).map((row) => (
              <div key={row.id} className="text-xs text-muted-foreground">
                {row.change_type} • {new Date(row.created_at).toLocaleString()}
              </div>
            ))
          )}
        </div>

        <div className="rounded-lg border border-border/70 p-3 space-y-2">
          <p className="text-sm font-medium text-foreground">Drift Alerts</p>
          {drifts.length === 0 ? (
            <p className="text-xs text-muted-foreground">No drift alerts right now.</p>
          ) : (
            drifts.slice(0, 10).map((row) => (
              <div key={row.goal_id} className="text-xs text-muted-foreground">
                {row.title} • score {row.drift_score} • {row.reason}
              </div>
            ))
          )}
        </div>
      </Card>

      {assignOpen && editor ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-3xl rounded-xl border bg-card p-5 space-y-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle>Assign Goal</CardTitle>
                <CardDescription>
                  Role filter: {roleLabel(editor.role)}. Only matching employees are shown.
                </CardDescription>
              </div>
              <Button variant="outline" onClick={() => setAssignOpen(false)}>Close</Button>
            </div>

            <div className="grid grid-cols-1 gap-3">
              <Input
                value={editor.title}
                onChange={(event) => setEditor((prev) => prev ? { ...prev, title: event.target.value } : prev)}
                placeholder="Goal title"
              />
              <Textarea
                value={editor.description}
                onChange={(event) => setEditor((prev) => prev ? { ...prev, description: event.target.value } : prev)}
                placeholder="Goal description"
              />
              <Input
                value={editor.kpi}
                onChange={(event) => setEditor((prev) => prev ? { ...prev, kpi: event.target.value } : prev)}
                placeholder="KPI (optional)"
              />
              <Input
                type="number"
                min={1}
                max={100}
                value={editor.weightage}
                onChange={(event) => {
                  const weight = Number(event.target.value || 0);
                  setEditor((prev) => prev ? { ...prev, weightage: weight } : prev);
                }}
                placeholder="Weightage"
              />
            </div>

            <div className="space-y-3">
              <p className="text-sm font-medium text-foreground inline-flex items-center gap-2">
                <Users className="h-4 w-4" /> Select Employee
              </p>

              {loadingCandidates ? (
                <p className="text-sm text-muted-foreground">Loading role-matched employees...</p>
              ) : candidates.length === 0 ? (
                <p className="text-sm text-muted-foreground">No role-matched employees available.</p>
              ) : (
                <div className="max-h-72 overflow-y-auto space-y-2">
                  {candidates.map((candidate) => {
                    const selected = selectedEmployeeId === candidate.employee_id;
                    return (
                      <button
                        key={candidate.employee_id}
                        type="button"
                        onClick={() => setSelectedEmployeeId(candidate.employee_id)}
                        className={`w-full rounded-lg border p-3 text-left transition ${selected ? "border-primary bg-primary/5" : "border-border/70 bg-card"}`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-foreground">{candidate.employee_name}</p>
                            <p className="text-xs text-muted-foreground">{candidate.role}</p>
                          </div>
                          <span className={`rounded-full px-2 py-0.5 text-xs ${workloadBadgeClass(candidate.workload_status)}`}>
                            {candidate.workload_status}
                          </span>
                        </div>

                        <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                          <p>Goals: {candidate.goal_count}</p>
                          <p>Workload: {candidate.workload_percent}%</p>
                          <p>Active check-ins: {candidate.active_checkins}</p>
                        </div>

                        <div className="mt-2 h-2 w-full rounded bg-muted/60">
                          <div
                            className={`h-2 rounded ${workloadColor(candidate.workload_percent)}`}
                            style={{ width: `${Math.min(candidate.workload_percent, 100)}%` }}
                          />
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <label className="inline-flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={allowOverload}
                onChange={(event) => setAllowOverload(event.target.checked)}
              />
              Allow assignment if workload exceeds 100%
            </label>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setAssignOpen(false)} disabled={assigning}>Cancel</Button>
              <Button onClick={submitAssignment} disabled={assigning || loadingCandidates}>Assign Goal</Button>
            </div>
          </Card>
        </div>
      ) : null}
    </motion.div>
  );
}

