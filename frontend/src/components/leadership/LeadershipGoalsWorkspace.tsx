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
import { hrService } from "@/services/hr";
import { leadershipGoalsService } from "@/services/leadership-goals";
import type { AOPManagerAssignment, AOPProgress, HRManagerOption, LeadershipAOPTarget } from "@/types";

interface LeadershipGoalsWorkspaceProps {
  initialView?: "aop" | "assignments" | "progress";
}

interface DraftAssignment {
  manager_id: string;
  target_value: number;
  target_percentage: number;
}

const currentYear = new Date().getFullYear();

export function LeadershipGoalsWorkspace({ initialView = "aop" }: LeadershipGoalsWorkspaceProps) {
  const [activeView, setActiveView] = useState<"aop" | "assignments" | "progress">(initialView);
  const [targets, setTargets] = useState<LeadershipAOPTarget[]>([]);
  const [managers, setManagers] = useState<HRManagerOption[]>([]);
  const [selectedAopId, setSelectedAopId] = useState<string>("");
  const [assignments, setAssignments] = useState<AOPManagerAssignment[]>([]);
  const [progress, setProgress] = useState<AOPProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [savingAop, setSavingAop] = useState(false);
  const [savingAssignments, setSavingAssignments] = useState(false);
  const [draftAssignments, setDraftAssignments] = useState<Record<string, DraftAssignment>>({});

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

  const selectedAop = useMemo(() => targets.find((item) => item.id === selectedAopId) ?? null, [targets, selectedAopId]);

  useEffect(() => {
    setActiveView(initialView);
  }, [initialView]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [aopTargets, managerRows] = await Promise.all([
          leadershipGoalsService.listAopTargets(),
          hrService.getManagers(),
        ]);
        setTargets(aopTargets);
        setManagers(managerRows);
        if (aopTargets.length > 0) {
          setSelectedAopId(aopTargets[0].id);
        }
      } catch {
        toast.error("Unable to load leadership goals workspace");
      } finally {
        setLoading(false);
      }
    };

    load().catch(() => null);
  }, []);

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
        managers: managers.map((manager) => ({
          manager_id: manager.id,
          manager_name: manager.name,
          department: manager.department ?? undefined,
        })),
      });

      const nextDraft: Record<string, DraftAssignment> = {};
      for (const row of response.assignments) {
        nextDraft[row.manager_id] = {
          manager_id: row.manager_id,
          target_value: Number(row.suggested_value.toFixed(2)),
          target_percentage: Number(row.suggested_percentage.toFixed(2)),
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leadership Goals"
        description="Create strategic AOP targets, assign manager-level ownership, and track cascading progress."
        action={
          <div className="flex items-center gap-2">
            <Button variant={activeView === "aop" ? "default" : "outline"} onClick={() => setActiveView("aop")}>AOP Targets</Button>
            <Button variant={activeView === "assignments" ? "default" : "outline"} onClick={() => setActiveView("assignments")}>Assignments</Button>
            <Button variant={activeView === "progress" ? "default" : "outline"} onClick={() => setActiveView("progress")}>Progress</Button>
          </div>
        }
      />

      <Card className="rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Active AOP Targets</CardTitle>
        <CardDescription>Select one AOP target as the working context for assignment and progress drilldowns.</CardDescription>
        <div className="mt-4 flex flex-wrap gap-2">
          {targets.map((target) => (
            <Button
              key={target.id}
              variant={target.id === selectedAopId ? "default" : "outline"}
              onClick={() => setSelectedAopId(target.id)}
              className="h-auto py-2"
            >
              {target.title} ({target.assigned_percentage.toFixed(1)}%)
            </Button>
          ))}
          {targets.length === 0 && !loading ? <p className="text-sm text-muted-foreground">No AOP targets yet.</p> : null}
        </div>
      </Card>

      {activeView === "aop" ? (
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Target className="h-3.5 w-3.5" /> Strategic Target Setup
          </div>
          <CardTitle>Create Leadership AOP Target</CardTitle>
          <CardDescription>Define the enterprise metric, value, and scope for this cycle.</CardDescription>

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

          <Button onClick={onCreateAop} disabled={savingAop}>{savingAop ? "Saving..." : "Create AOP Target"}</Button>
        </Card>
      ) : null}

      {activeView === "assignments" ? (
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Manager Allocation</CardTitle>
              <CardDescription>Split the selected target across managers by value and percentage.</CardDescription>
            </div>
            <Button variant="outline" onClick={applyAiDistribution} disabled={!selectedAop || managers.length === 0}>
              <Sparkles className="mr-2 h-4 w-4" /> Suggest with AI
            </Button>
          </div>

          <div className="space-y-3">
            {managers.map((manager) => {
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
          </div>

          <Button onClick={saveAssignments} disabled={savingAssignments || !selectedAopId}>
            {savingAssignments ? "Saving..." : "Save Assignments"}
          </Button>

          <div className="space-y-2 pt-2">
            <p className="text-sm font-semibold text-foreground">Current Assignment Status</p>
            {assignments.length === 0 ? <p className="text-sm text-muted-foreground">No manager assignments yet.</p> : null}
            {assignments.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-lg border border-border/70 px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{item.manager_name}</p>
                  <p className="text-xs text-muted-foreground">{item.assigned_target_value} {item.target_unit || "units"}</p>
                </div>
                <Badge>{item.assigned_percentage.toFixed(1)}%</Badge>
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
                  <p className="text-muted-foreground">{progress.achieved_value.toFixed(2)} / {progress.total_target_value.toFixed(2)}</p>
                </div>
                <Progress className="mt-3" value={progress.achieved_percentage} />
                <p className="mt-2 text-xs text-muted-foreground">{progress.achieved_percentage.toFixed(1)}% of leadership target achieved</p>
              </div>

              <div className="space-y-3">
                {progress.managers.map((row) => (
                  <div key={row.manager_id} className="rounded-lg border border-border/70 p-3">
                    <div className="flex items-center justify-between text-sm">
                      <p className="font-medium text-foreground">{row.manager_name}</p>
                      <Badge>{row.status_label}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Target: {row.target_value.toFixed(2)} | Achieved: {row.achieved_value.toFixed(2)}
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
