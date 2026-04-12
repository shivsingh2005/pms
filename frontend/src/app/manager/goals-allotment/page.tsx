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
import { aiService } from "@/services/ai";
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

interface GoalEditorState {
  role: string;
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

function roleLabel(role: string): string {
  const trimmed = role.trim();
  if (!trimmed) return "General";
  if (!/[\s_-]/.test(trimmed)) {
    return trimmed;
  }
  return trimmed
    .replace(/[_-]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeRoleKey(value: string): string {
  return (value || "").trim().toLowerCase().replace(/[_-]+/g, " ");
}

function buildFallbackClusters(teamMembers: ManagerTeamMember[]): RoleGoalCluster[] {
  const roleToMembers = new Map<string, ManagerTeamMember[]>();

  for (const member of teamMembers) {
    const role = (member.role || "General").trim() || "General";
    const bucket = roleToMembers.get(role) || [];
    bucket.push(member);
    roleToMembers.set(role, bucket);
  }

  const clusters: RoleGoalCluster[] = [];
  for (const [role, members] of Array.from(roleToMembers.entries())) {
    const teamSize = members.length;
    clusters.push({
      role,
      goals: [
        {
          title: `Improve ${roleLabel(role)} delivery reliability`,
          description: `Increase predictable execution for ${roleLabel(role)} outcomes with clear sprint commitments and risk tracking.`,
          difficulty: "medium",
          suggested_weight: 35,
          kpi: `Maintain at least 90% commitment reliability across ${teamSize} team member(s)`,
        },
        {
          title: `Raise quality standards for ${roleLabel(role)}`,
          description: `Reduce defects and rework by improving review quality and pre-release validation discipline.`,
          difficulty: "medium",
          suggested_weight: 30,
          kpi: `Reduce escaped defects by 20% this cycle`,
        },
        {
          title: `Strengthen cross-functional collaboration`,
          description: `Resolve handoff bottlenecks with adjacent teams and improve end-to-end ownership.`,
          difficulty: "hard",
          suggested_weight: 35,
          kpi: `Close at least 2 cross-team dependencies with measurable impact`,
        },
      ],
    });
  }

  return clusters;
}

export default function ManagerGoalsAllotmentPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const setActiveMode = useSessionStore((s) => s.setActiveMode);

  const [objective, setObjective] = useState("");
  const [generating, setGenerating] = useState(false);
  const [clusters, setClusters] = useState<RoleGoalCluster[]>([]);
  const [activeRole, setActiveRole] = useState("");

  const [assignOpen, setAssignOpen] = useState(false);
  const [editor, setEditor] = useState<GoalEditorState | null>(null);
  const [candidates, setCandidates] = useState<GoalAssignmentCandidate[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [roleCandidates, setRoleCandidates] = useState<GoalAssignmentCandidate[]>([]);
  const [loadingRoleCandidates, setLoadingRoleCandidates] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [allowOverload, setAllowOverload] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const [managerGoals, setManagerGoals] = useState<Goal[]>([]);
  const [teamMembers, setTeamMembers] = useState<ManagerTeamMember[]>([]);
  const [parentGoalId, setParentGoalId] = useState("");
  const [cascadeTargets, setCascadeTargets] = useState<CascadeTargetState[]>([]);
  const [cascading, setCascading] = useState(false);
  const [subgoals, setSubgoals] = useState<string[]>([]);
  const [breakingSubgoals, setBreakingSubgoals] = useState(false);

  const [drifts, setDrifts] = useState<GoalDriftInsight[]>([]);
  const [lineageGoalId, setLineageGoalId] = useState("");
  const [lineage, setLineage] = useState<GoalLineage | null>(null);
  const [changeLogs, setChangeLogs] = useState<GoalChangeLog[]>([]);

  const buildFallbackCandidates = useCallback(
    (roleFilter?: string): GoalAssignmentCandidate[] => {
      const normalizedFilter = normalizeRoleKey(roleFilter || "");

      const filteredTeam = normalizedFilter && normalizedFilter !== "general"
        ? teamMembers.filter((member) => {
            const memberRole = normalizeRoleKey(member.role);
            return memberRole === normalizedFilter || memberRole.includes(normalizedFilter) || normalizedFilter.includes(memberRole);
          })
        : teamMembers;

      const source = filteredTeam.length > 0 ? filteredTeam : teamMembers;

      return source.map((member) => {
        const workload = Number(member.current_workload || 0);
        return {
          employee_id: member.id,
          employee_name: member.name,
          role: member.role,
          role_key: normalizeRoleKey(member.role),
          goal_count: Number(member.current_goals_count || 0),
          total_weightage: workload,
          active_checkins: 0,
          workload_percent: workload,
          workload_status: workload < 50 ? "low" : workload < 80 ? "medium" : "high",
        };
      });
    },
    [teamMembers],
  );

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

  const roleOrder = useMemo(() => {
    return clusters
      .map((cluster) => cluster.role.trim())
      .filter((role, index, arr) => role.length > 0 && arr.indexOf(role) === index);
  }, [clusters]);

  const clusterMap = useMemo(() => {
    const map: Record<string, RoleGoalRecommendation[]> = {};
    for (const cluster of clusters) {
      const key = cluster.role.trim();
      if (!key) continue;
      map[key] = cluster.goals || [];
    }
    return map;
  }, [clusters]);

  useEffect(() => {
    if (roleOrder.length === 0) {
      setActiveRole("");
      return;
    }

    if (!activeRole || !roleOrder.includes(activeRole)) {
      setActiveRole(roleOrder[0]);
    }
  }, [activeRole, roleOrder]);

  useEffect(() => {
    if (!activeRole) {
      setRoleCandidates([]);
      return;
    }

    const loadRoleCandidates = async () => {
      setLoadingRoleCandidates(true);
      try {
        const rows = await goalsService.getAssignmentCandidates(activeRole);
        setRoleCandidates(rows);
      } catch {
        setRoleCandidates([]);
      } finally {
        setLoadingRoleCandidates(false);
      }
    };

    void loadRoleCandidates();
  }, [activeRole]);

  const visibleGoals = activeRole ? clusterMap[activeRole] || [] : [];

  const generateRoleClusters = async () => {
    setGenerating(true);
    try {
      const payload = await goalsService.getAssignmentRecommendations({
        organization_objectives: objective.trim() || undefined,
      });
      const apiClusters = payload.clusters || [];
      const usableClusters = apiClusters.some((cluster) => (cluster.goals || []).length > 0)
        ? apiClusters
        : buildFallbackClusters(teamMembers);

      setClusters(usableClusters);
      const firstRole = usableClusters.find((cluster) => cluster.role.trim())?.role || "";
      setActiveRole(firstRole);
      if (usableClusters === apiClusters) {
        toast.success("Role-based AI goal clusters generated");
      } else {
        toast.warning("AI returned no role goals. Generated fallback role clusters from team structure.");
      }
    } catch (error: unknown) {
      const fallbackClusters = buildFallbackClusters(teamMembers);
      if (fallbackClusters.length > 0) {
        setClusters(fallbackClusters);
        setActiveRole(fallbackClusters[0].role);
        toast.warning("AI generation failed. Showing fallback role clusters from your team.");
      }

      const message =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      if (fallbackClusters.length === 0) {
        toast.error(message || "Failed to generate role-based goal clusters");
      }
    } finally {
      setGenerating(false);
    }
  };

  const openAssignModal = async (role: string, goal: RoleGoalRecommendation) => {
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
      setCandidates(rows.length > 0 ? rows : buildFallbackCandidates(role));
    } catch {
      setCandidates(buildFallbackCandidates(role));
      toast.error("Role match unavailable. Showing team members instead.");
    } finally {
      setLoadingCandidates(false);
    }
  };

  const openManualAssignModal = async () => {
    const role = activeRole || "General";
    setEditor({
      role,
      title: "",
      description: "",
      kpi: "",
      weightage: 25,
    });
    setAssignOpen(true);
    setSelectedEmployeeId("");
    setAllowOverload(false);

    setLoadingCandidates(true);
    try {
      const rows = await goalsService.getAssignmentCandidates(role);
      setCandidates(rows.length > 0 ? rows : buildFallbackCandidates(role));
    } catch {
      setCandidates(buildFallbackCandidates(role));
      toast.error("Role match unavailable. Showing team members instead.");
    } finally {
      setLoadingCandidates(false);
    }
  };

  const breakGoalIntoSubgoals = async () => {
    if (!editor) {
      toast.error("Pick an AI cluster goal or create a manual goal first");
      return;
    }

    const selectedTargets = cascadeTargets.filter((row) => row.selected);
    const expectedSubgoalCount = Math.max(selectedTargets.length, 3);

    setBreakingSubgoals(true);
    try {
      const prompt = [
        "Break this manager goal into concise execution subgoals for team allocation.",
        `Role: ${editor.role}`,
        `Goal Title: ${editor.title}`,
        `Goal Description: ${editor.description}`,
        `KPI: ${editor.kpi || "N/A"}`,
        `Create ${expectedSubgoalCount} subgoals as a plain numbered list.`,
        "Each line should be only the subgoal title.",
      ].join("\n");

      const response = await aiService.ask(prompt, "manager-goals-allotment");
      const parsed = String(response.response || "")
        .split("\n")
        .map((line) => line.replace(/^\s*(?:[-*]|\d+[.)])\s*/, "").trim())
        .filter((line) => line.length > 0)
        .slice(0, expectedSubgoalCount);

      if (parsed.length === 0) {
        toast.error("AI could not generate subgoals. Please try again.");
        return;
      }

      setSubgoals(parsed);
      toast.success(`Generated ${parsed.length} subgoals with AI`);
    } catch {
      toast.error("Failed to generate subgoals with AI");
    } finally {
      setBreakingSubgoals(false);
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
      setRoleCandidates(refreshed);
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
      const seededSubgoals = subgoals.filter((item) => item.trim().length > 0);
      const result = await goalsService.cascadeGoal({
        parent_goal_id: parentGoalId,
        normalize_weights: true,
        children: selectedTargets.map((row, index) => {
          const subgoalTitle = seededSubgoals[index % seededSubgoals.length];
          return {
            employee_id: row.employee_id,
            title: subgoalTitle || editor.title,
            description: subgoalTitle
              ? `${editor.description}\n\nSubgoal focus: ${subgoalTitle}`
              : editor.description,
            kpi: editor.kpi || undefined,
            framework: "OKR",
            weightage: row.contribution_weight,
            progress: 0,
          };
        }),
      });

      toast.success(`Cascaded to ${result.children_created} team members`);
      const driftRows = await goalsService.getGoalDriftInsights();
      setDrifts(driftRows);
      setSubgoals([]);
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
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => void openManualAssignModal()}>
              Create Goal Manually
            </Button>
            <Button onClick={generateRoleClusters} disabled={generating}>
              <Sparkles className="mr-2 h-4 w-4" />
              {generating ? "Generating..." : "Generate Role Clusters"}
            </Button>
          </div>
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
          {roleOrder.map((role) => (
            <Button
              key={role}
              variant={activeRole === role ? "default" : "outline"}
              onClick={() => setActiveRole(role)}
            >
              {roleLabel(role)}
            </Button>
          ))}
        </div>

        {roleOrder.length === 0 ? (
          <p className="text-sm text-muted-foreground">Generate clusters to view AI-identified role groups.</p>
        ) : null}

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

        <div className="rounded-lg border border-border/70 p-4 space-y-3">
          <p className="text-sm font-medium text-foreground">Employees in {roleLabel(activeRole)} and current workload</p>
          {loadingRoleCandidates ? (
            <p className="text-sm text-muted-foreground">Loading employees for selected role...</p>
          ) : roleCandidates.length === 0 ? (
            <p className="text-sm text-muted-foreground">No employees found for this role.</p>
          ) : (
            <div className="space-y-2">
              {roleCandidates.map((candidate) => (
                <div key={`role-${candidate.employee_id}`} className="rounded-lg border border-border/70 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-foreground">{candidate.employee_name}</p>
                      <p className="text-xs text-muted-foreground">{candidate.role}</p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${workloadBadgeClass(candidate.workload_status)}`}>
                      {candidate.workload_percent}%
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full rounded bg-muted/60">
                    <div
                      className={`h-2 rounded ${workloadColor(candidate.workload_percent)}`}
                      style={{ width: `${Math.min(candidate.workload_percent, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
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

        <div className="rounded-lg border border-border/70 p-3 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-foreground">AI Subgoal Breakdown (before allocation)</p>
            <Button variant="outline" onClick={() => void breakGoalIntoSubgoals()} disabled={breakingSubgoals || !editor}>
              <Sparkles className="mr-2 h-4 w-4" />
              {breakingSubgoals ? "Breaking..." : "Break into Subgoals"}
            </Button>
          </div>

          {subgoals.length === 0 ? (
            <p className="text-xs text-muted-foreground">Generate subgoals with AI to cascade granular child goals to selected team members.</p>
          ) : (
            <div className="space-y-2">
              {subgoals.map((subgoal, index) => (
                <Input
                  key={`subgoal-${index}`}
                  value={subgoal}
                  onChange={(event) => {
                    const value = event.target.value;
                    setSubgoals((prev) => prev.map((item, idx) => (idx === index ? value : item)));
                  }}
                  placeholder={`Subgoal ${index + 1}`}
                />
              ))}
            </div>
          )}
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
        <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center overflow-y-auto bg-black/60 p-4">
          <Card className="my-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-xl border bg-card p-5 space-y-4">
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
                <>
                  <select
                    className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
                    value={selectedEmployeeId}
                    onChange={(event) => setSelectedEmployeeId(event.target.value)}
                  >
                    <option value="">Choose employee</option>
                    {candidates.map((candidate) => (
                      <option key={candidate.employee_id} value={candidate.employee_id}>
                        {candidate.employee_name} ({candidate.role})
                      </option>
                    ))}
                  </select>
                  {selectedEmployeeId ? (
                    <p className="text-xs text-muted-foreground">
                      Selected: {candidates.find((candidate) => candidate.employee_id === selectedEmployeeId)?.employee_name || "Employee"}
                    </p>
                  ) : null}
                </>
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
              <Button
                variant="outline"
                onClick={() => setAssignOpen(false)}
                disabled={assigning}
              >
                Cancel
              </Button>
              <Button onClick={submitAssignment} disabled={assigning || loadingCandidates}>Assign Goal</Button>
            </div>
          </Card>
        </div>
      ) : null}
    </motion.div>
  );
}

