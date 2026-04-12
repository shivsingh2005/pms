"use client";

import { useEffect, useMemo, useState } from "react";
import { Sparkles, Target } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { aiService } from "@/services/ai";
import { goalsService } from "@/services/goals";
import { hrService } from "@/services/hr";
import { leadershipGoalsService } from "@/services/leadership-goals";
import type { AOPManagerAssignment, AOPProgress, Goal, HRManagerOption, LeadershipAOPTarget } from "@/types";
import { fixed } from "@/lib/safe";
import { useSessionStore } from "@/store/useSessionStore";

interface LeadershipGoalsWorkspaceProps {
  initialView?: "aop" | "assignments" | "progress";
}

interface DraftAssignment {
  manager_id: string;
  target_value: number;
  target_percentage: number;
}

interface ManagerGoalCascadeDraft {
  manager_id: string;
  selected: boolean;
  weightage: number;
}

interface AssignableManagerOption {
  id: string;
  name: string;
  department?: string | null;
}

const currentYear = new Date().getFullYear();

export function LeadershipGoalsWorkspace({ initialView = "aop" }: LeadershipGoalsWorkspaceProps) {
  const [activeView, setActiveView] = useState<"aop" | "assignments" | "progress">(initialView);
  const currentUser = useSessionStore((state) => state.user);
  const [targets, setTargets] = useState<LeadershipAOPTarget[]>([]);
  const [managers, setManagers] = useState<HRManagerOption[]>([]);
  const [selectedAopId, setSelectedAopId] = useState<string>("");
  const [assignments, setAssignments] = useState<AOPManagerAssignment[]>([]);
  const [progress, setProgress] = useState<AOPProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [goalSaving, setGoalSaving] = useState(false);
  const [savingAop, setSavingAop] = useState(false);
  const [savingAssignments, setSavingAssignments] = useState(false);
  const [cascadingGoals, setCascadingGoals] = useState(false);
  const [draftAssignments, setDraftAssignments] = useState<Record<string, DraftAssignment>>({});
  const [goalCascadeDraft, setGoalCascadeDraft] = useState<Record<string, ManagerGoalCascadeDraft>>({});
  const [leadershipGoals, setLeadershipGoals] = useState<Goal[]>([]);
  const [selectedLeadershipGoalId, setSelectedLeadershipGoalId] = useState("");

  const [goalForm, setGoalForm] = useState({
    title: "",
    description: "",
    weightage: 20,
    framework: "OKR" as "OKR" | "MBO" | "Hybrid",
  });

  const [form, setForm] = useState({
    title: "",
    description: "",
    total_target_value: 100,
    target_unit: "units",
    target_metric: "Business impact",
    year: currentYear,
    quarter: 1,
    department: "",
  });

  const filteredTargets = targets;

  const selectedAop = useMemo(() => filteredTargets.find((item) => item.id === selectedAopId) ?? null, [filteredTargets, selectedAopId]);

  useEffect(() => {
    setActiveView(initialView);
  }, [initialView]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [aopResult, managerResult, goalsResult] = await Promise.allSettled([
        leadershipGoalsService.listAopTargets(),
        hrService.getManagers(),
        goalsService.getGoals(),
      ]);

      if (aopResult.status === "fulfilled") {
        const aopTargets = aopResult.value;
        setTargets(aopTargets);
        if (aopTargets.length > 0) {
          setSelectedAopId(aopTargets[0].id);
        }
      }

      if (managerResult.status === "fulfilled") {
        setManagers(managerResult.value);
      } else {
        setManagers([]);
        toast.error("Unable to load managers from database");
      }

      if (goalsResult.status === "fulfilled") {
        const allGoals = goalsResult.value.filter((goal) => goal.user_id === currentUser?.id);
        setLeadershipGoals(allGoals);
        if (allGoals.length > 0) {
          setSelectedLeadershipGoalId((prev) => prev || allGoals[0].id);
        }
      } else {
        setLeadershipGoals([]);
      }

      setLoading(false);
    };

    load().catch(() => null);
  }, [currentUser?.id]);

  useEffect(() => {
    if (filteredTargets.length === 0) {
      setSelectedAopId("");
      return;
    }
    if (!filteredTargets.some((item) => item.id === selectedAopId)) {
      setSelectedAopId(filteredTargets[0].id);
    }
  }, [filteredTargets, selectedAopId]);

  useEffect(() => {
    if (!selectedAopId) {
      setAssignments([]);
      setProgress(null);
      return;
    }

    const loadAopDetails = async () => {
      try {
        const [assignmentRows, progressRow] = await Promise.all([
          leadershipGoalsService.listAssignments(selectedAopId),
          leadershipGoalsService.getProgress(selectedAopId),
        ]);
        setAssignments(assignmentRows);
        setProgress(progressRow);
      } catch {
        toast.error("Unable to load assignments and progress");
      }
    };

    loadAopDetails().catch(() => null);
  }, [selectedAopId]);

  const onCreateAop = async () => {
    if (form.title.trim().length < 3) {
      toast.error("AOP title should be at least 3 characters");
      return;
    }

    setSavingAop(true);
    try {
      const created = await leadershipGoalsService.createAopTarget({
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        total_target_value: Number(form.total_target_value),
        target_unit: form.target_unit.trim(),
        target_metric: form.target_metric.trim(),
        year: Number(form.year),
        quarter: Number(form.quarter) || undefined,
        department: form.department.trim() || undefined,
      });
      const refreshed = await leadershipGoalsService.listAopTargets();
      setTargets(refreshed);
      setSelectedAopId(created.id);
      toast.success("AOP target created");
    } catch {
      toast.error("Unable to create AOP target");
    } finally {
      setSavingAop(false);
    }
  };

  const setDraftValue = (managerId: string, patch: Partial<DraftAssignment>) => {
    setDraftAssignments((prev) => {
      const existing = prev[managerId] ?? { manager_id: managerId, target_percentage: 0, target_value: 0 };
      return {
        ...prev,
        [managerId]: {
          ...existing,
          ...patch,
        },
      };
    });
  };

  const createLeadershipGoal = async () => {
    if (goalForm.title.trim().length < 3) {
      toast.error("Goal title should be at least 3 characters");
      return;
    }

    setGoalSaving(true);
    try {
      await goalsService.createGoal({
        title: goalForm.title.trim(),
        description: goalForm.description.trim() || undefined,
        weightage: Number(goalForm.weightage),
        progress: 0,
        framework: goalForm.framework,
      });
      const allGoals = await goalsService.getGoals();
      setLeadershipGoals(allGoals);
      if (!selectedLeadershipGoalId && allGoals.length > 0) {
        setSelectedLeadershipGoalId(allGoals[0].id);
      }
      toast.success("Leadership goal created");
      setGoalForm({ title: "", description: "", weightage: 20, framework: "OKR" });
    } catch {
      toast.error("Unable to create leadership goal");
    } finally {
      setGoalSaving(false);
    }
  };

  const applyAiDistribution = async () => {
    if (!selectedAop) {
      toast.error("Choose an AOP target first");
      return;
    }

    try {
      const response = await aiService.suggestAopDistribution({
        total_target_value: selectedAop.total_target_value,
        target_unit: selectedAop.target_unit,
        target_metric: selectedAop.target_metric,
        managers: assignableManagers.map((manager) => ({
          manager_id: manager.id,
          manager_name: manager.name,
          department: manager.department ?? undefined,
        })),
      });

      const nextDraft: Record<string, DraftAssignment> = {};
      for (const row of response.assignments) {
        nextDraft[row.manager_id] = {
          manager_id: row.manager_id,
          target_value: Number(fixed(row.suggested_value, 2)),
          target_percentage: Number(fixed(row.suggested_percentage, 2)),
        };
      }
      setDraftAssignments(nextDraft);
      toast.success("AI distribution applied to assignment draft");
    } catch {
      toast.error("Unable to generate AI manager distribution");
    }
  };

  const saveAssignments = async () => {
    if (!selectedAopId) {
      toast.error("Select an AOP target first");
      return;
    }

    const payload = Object.values(draftAssignments).filter((item) => item.target_percentage > 0 || item.target_value > 0);
    if (payload.length === 0) {
      toast.error("Enter at least one manager assignment");
      return;
    }

    setSavingAssignments(true);
    try {
      await leadershipGoalsService.assignManagers(selectedAopId, payload);
      const [assignmentRows, progressRow, refreshedTargets] = await Promise.all([
        leadershipGoalsService.listAssignments(selectedAopId),
        leadershipGoalsService.getProgress(selectedAopId),
        leadershipGoalsService.listAopTargets(),
      ]);
      setAssignments(assignmentRows);
      setProgress(progressRow);
      setTargets(refreshedTargets);
      toast.success("Manager targets assigned");
    } catch {
      toast.error("Unable to assign managers");
    } finally {
      setSavingAssignments(false);
    }
  };

  const selectedLeadershipGoal = useMemo(
    () => leadershipGoals.find((goal) => goal.id === selectedLeadershipGoalId) ?? null,
    [leadershipGoals, selectedLeadershipGoalId],
  );

  const assignableManagers = useMemo<AssignableManagerOption[]>(() => {
    const managerMap = new Map<string, AssignableManagerOption>();
    for (const manager of managers) {
      managerMap.set(manager.id, {
        id: manager.id,
        name: manager.name,
        department: manager.department || null,
      });
    }
    for (const row of assignments) {
      if (!managerMap.has(row.manager_id)) {
        managerMap.set(row.manager_id, {
          id: row.manager_id,
          name: row.manager_name,
          department: row.manager_department || null,
        });
      }
    }
    return Array.from(managerMap.values());
  }, [assignments, managers]);

  const updateGoalCascadeDraft = (managerId: string, patch: Partial<ManagerGoalCascadeDraft>) => {
    setGoalCascadeDraft((prev) => {
      const existing = prev[managerId] ?? { manager_id: managerId, selected: false, weightage: 0 };
      return {
        ...prev,
        [managerId]: {
          ...existing,
          ...patch,
        },
      };
    });
  };

  const seedGoalCascadeFromAssignments = () => {
    const seeded: Record<string, ManagerGoalCascadeDraft> = {};
    for (const manager of assignableManagers) {
      const fromAssignment = draftAssignments[manager.id];
      const weightage = Number(fromAssignment?.target_percentage || 0);
      seeded[manager.id] = {
        manager_id: manager.id,
        selected: weightage > 0,
        weightage,
      };
    }
    setGoalCascadeDraft(seeded);
    toast.success("Copied current manager split into goal assignment draft");
  };

  const cascadeLeadershipGoalToManagers = async () => {
    if (!selectedLeadershipGoal) {
      toast.error("Create or choose a leadership goal first");
      return;
    }

    const selectedRows = Object.values(goalCascadeDraft).filter((row) => row.selected && row.weightage > 0);
    if (selectedRows.length === 0) {
      toast.error("Choose at least one manager and assign weightage");
      return;
    }

    const managerById = new Map(assignableManagers.map((manager) => [manager.id, manager]));

    setCascadingGoals(true);
    try {
      const payload = selectedRows.map((row) => {
        const manager = managerById.get(row.manager_id);
        return {
          employee_id: row.manager_id,
          title: `${selectedLeadershipGoal.title} - ${manager?.name ?? "Manager"}`,
          description: selectedLeadershipGoal.description || undefined,
          framework: selectedLeadershipGoal.framework,
          weightage: row.weightage,
          progress: 0,
        };
      });

      const result = await goalsService.cascadeGoal({
        parent_goal_id: selectedLeadershipGoal.id,
        normalize_weights: true,
        children: payload,
      });

      toast.success(`Assigned and cascaded to ${result.children_created} manager goals`);
      setGoalCascadeDraft({});
    } catch {
      toast.error("Unable to cascade leadership goal to managers");
    } finally {
      setCascadingGoals(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leadership Goals"
        description="Create leadership goals and cascade them to managers to complete the leadership-to-manager cycle."
        action={
          <div className="flex items-center gap-2">
            <Button variant={activeView === "aop" ? "default" : "outline"} onClick={() => setActiveView("aop")}>AOP Targets</Button>
            <Button variant={activeView === "assignments" ? "default" : "outline"} onClick={() => setActiveView("assignments")}>Assignments</Button>
            <Button variant={activeView === "progress" ? "default" : "outline"} onClick={() => setActiveView("progress")}>Progress</Button>
            <Button variant="outline" onClick={() => setActiveView("aop")}>Create Goal</Button>
          </div>
        }
      />

      {activeView === "aop" ? (
        <>
          <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Target className="h-3.5 w-3.5" /> Strategic Target Setup
            </div>
            <CardTitle>Create Cascade Target</CardTitle>
            <CardDescription>Define the enterprise metric, value, and scope before cascading it to relevant managers.</CardDescription>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input placeholder="Title" value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} />
              <Input
                placeholder="Department (optional)"
                value={form.department}
                onChange={(event) => setForm((prev) => ({ ...prev, department: event.target.value }))}
              />
              <Input
                type="number"
                placeholder="Total target value"
                value={form.total_target_value}
                onChange={(event) => setForm((prev) => ({ ...prev, total_target_value: Number(event.target.value) || 0 }))}
              />
              <Input placeholder="Target unit" value={form.target_unit} onChange={(event) => setForm((prev) => ({ ...prev, target_unit: event.target.value }))} />
              <Input
                placeholder="Target metric"
                value={form.target_metric}
                onChange={(event) => setForm((prev) => ({ ...prev, target_metric: event.target.value }))}
              />
              <div className="grid grid-cols-2 gap-2">
                <Input type="number" value={form.year} onChange={(event) => setForm((prev) => ({ ...prev, year: Number(event.target.value) || currentYear }))} />
                <Input type="number" min={1} max={4} value={form.quarter} onChange={(event) => setForm((prev) => ({ ...prev, quarter: Number(event.target.value) || 1 }))} />
              </div>
            </div>

            <Textarea
              placeholder="Describe business context and expected outcomes"
              value={form.description}
              onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            />

            <Button onClick={onCreateAop} disabled={savingAop}>{savingAop ? "Saving..." : "Create Cascade Target"}</Button>
          </Card>
        </>
      ) : null}

      {activeView === "assignments" || activeView === "progress" ? (
        <Card className="rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Active Strategic Targets</CardTitle>
          <CardDescription>Select one target as the working context for cascade assignment and progress drilldowns.</CardDescription>
          <div className="mt-4 flex flex-wrap gap-2">
            {filteredTargets.map((target) => (
              <Button
                key={target.id}
                variant={target.id === selectedAopId ? "default" : "outline"}
                onClick={() => setSelectedAopId(target.id)}
                className="h-auto py-2"
              >
                {target.title} ({fixed(target.assigned_percentage, 1)}%)
              </Button>
            ))}
            {filteredTargets.length === 0 && !loading ? <p className="text-sm text-muted-foreground">No AOP targets found for this cycle.</p> : null}
          </div>
        </Card>
      ) : null}

      {activeView === "assignments" ? (
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Cascade to Relevant Managers</CardTitle>
              <CardDescription>Split the selected target across the managers who should own execution.</CardDescription>
            </div>
            <Button variant="outline" onClick={applyAiDistribution} disabled={!selectedAop || assignableManagers.length === 0}>
              <Sparkles className="mr-2 h-4 w-4" /> Suggest Manager Split
            </Button>
          </div>

          <div className="space-y-3">
            {assignableManagers.map((manager) => {
              const draft = draftAssignments[manager.id] ?? { manager_id: manager.id, target_value: 0, target_percentage: 0 };
              return (
                <div key={manager.id} className="grid grid-cols-1 gap-3 rounded-xl border border-border/70 p-3 md:grid-cols-[1.2fr_1fr_1fr]">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{manager.name}</p>
                    <p className="text-xs text-muted-foreground">{manager.department || "No department"}</p>
                  </div>
                  <Input
                    type="number"
                    value={draft.target_value}
                    onChange={(event) => setDraftValue(manager.id, { target_value: Number(event.target.value) || 0 })}
                    placeholder="Target value"
                  />
                  <Input
                    type="number"
                    value={draft.target_percentage}
                    onChange={(event) => setDraftValue(manager.id, { target_percentage: Number(event.target.value) || 0 })}
                    placeholder="Target %"
                  />
                </div>
              );
            })}
            {assignableManagers.length === 0 ? <p className="text-sm text-warning">No managers available for manual assignment.</p> : null}
          </div>

          <Button onClick={saveAssignments} disabled={savingAssignments || !selectedAopId}>
            {savingAssignments ? "Saving..." : "Save Assignments"}
          </Button>

          <div className="space-y-3 rounded-xl border border-border/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-foreground">Goal Assignment Section</p>
                <p className="text-xs text-muted-foreground">Pick one leadership goal and assign it to managers, similar to manager-to-employee cascade.</p>
              </div>
              <Button variant="outline" size="sm" onClick={seedGoalCascadeFromAssignments}>
                Use Current Split
              </Button>
            </div>

            <select
              value={selectedLeadershipGoalId}
              onChange={(event) => setSelectedLeadershipGoalId(event.target.value)}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none"
            >
              <option value="">Select leadership goal</option>
              {leadershipGoals.map((goal) => (
                <option key={goal.id} value={goal.id}>{goal.title}</option>
              ))}
            </select>

            {assignableManagers.map((manager) => {
              const row = goalCascadeDraft[manager.id] ?? { manager_id: manager.id, selected: false, weightage: 0 };
              return (
                <div key={`cascade-${manager.id}`} className="grid grid-cols-1 gap-2 rounded-lg border border-border/60 p-3 md:grid-cols-[1.4fr_auto_140px]">
                  <div>
                    <p className="text-sm font-medium text-foreground">{manager.name}</p>
                    <p className="text-xs text-muted-foreground">{manager.department || "No department"}</p>
                  </div>
                  <label className="flex items-center gap-2 text-xs text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={row.selected}
                      onChange={(event) => updateGoalCascadeDraft(manager.id, { selected: event.target.checked })}
                    />
                    Include
                  </label>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={row.weightage}
                    onChange={(event) => updateGoalCascadeDraft(manager.id, { weightage: Number(event.target.value) || 0 })}
                    placeholder="Weight %"
                  />
                </div>
              );
            })}
            {assignableManagers.length === 0 ? <p className="text-xs text-warning">No managers found in this organization yet.</p> : null}

            <Button onClick={cascadeLeadershipGoalToManagers} disabled={cascadingGoals || !selectedLeadershipGoalId}>
              {cascadingGoals ? "Cascading..." : "Assign and Cascade Goal to Managers"}
            </Button>
          </div>

          <div className="space-y-2 pt-2">
            <p className="text-sm font-semibold text-foreground">Current Assignment Status</p>
            {assignments.length === 0 ? <p className="text-sm text-muted-foreground">No manager assignments yet.</p> : null}
            {assignments.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-lg border border-border/70 px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{item.manager_name}</p>
                  <p className="text-xs text-muted-foreground">{item.assigned_target_value} {item.target_unit || "units"}</p>
                </div>
                <Badge>{fixed(item.assigned_percentage, 1)}%</Badge>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {activeView === "progress" ? (
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
          <CardTitle>Cascade Progress</CardTitle>
          <CardDescription>Track how manager execution contributes to the enterprise target.</CardDescription>
          {!progress ? (
            <p className="text-sm text-muted-foreground">Select an AOP target to see progress.</p>
          ) : (
            <>
              <div className="rounded-xl border border-border/70 p-4">
                <div className="flex items-center justify-between text-sm">
                  <p className="font-medium text-foreground">{progress.title}</p>
                  <p className="text-muted-foreground">{fixed(progress.achieved_value, 2)} / {fixed(progress.total_target_value, 2)}</p>
                </div>
                <Progress className="mt-3" value={progress.achieved_percentage} />
                <p className="mt-2 text-xs text-muted-foreground">{fixed(progress.achieved_percentage, 1)}% of leadership target achieved</p>
              </div>

              <div className="space-y-3">
                {progress.managers.map((row) => (
                  <div key={row.manager_id} className="rounded-lg border border-border/70 p-3">
                    <div className="flex items-center justify-between text-sm">
                      <p className="font-medium text-foreground">{row.manager_name}</p>
                      <Badge>{row.status_label}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Target: {fixed(row.target_value, 2)} | Achieved: {fixed(row.achieved_value, 2)}
                    </p>
                    <Progress className="mt-2" value={row.achieved_percentage} />
                  </div>
                ))}
                {progress.managers.length === 0 ? <p className="text-sm text-muted-foreground">No manager progress records yet.</p> : null}
              </div>
            </>
          )}
        </Card>
      ) : null}
    </div>
  );
}
