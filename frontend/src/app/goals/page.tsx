"use client";

import { useEffect, useState } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Sparkles, Target, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { Progress } from "@/components/ui/progress";
import { GoalCard } from "@/components/goals/GoalCard";
import { GoalTimeline } from "@/components/goals/GoalTimeline";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { Skeleton } from "@/components/ui/skeleton";
import { aiService } from "@/services/ai";
import { goalsService } from "@/services/goals";
import { leadershipGoalsService } from "@/services/leadership-goals";
import { managerService } from "@/services/manager";
import { useGoalsStore } from "@/store/useGoalsStore";
import { useSessionStore } from "@/store/useSessionStore";
import type {
  AIGeneratedGoal,
  CascadedEmployeeGoal,
  CascadedManagerGoal,
  EmployeeCascadeSuggestion,
  GoalLineageImpact,
  ManagerPendingGoal,
  ManagerTeamMember,
  SelfGoalSummary,
} from "@/types";
import { toast } from "sonner";

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === "object") {
    const maybeAxios = error as {
      response?: { data?: { error?: unknown; message?: unknown } };
      message?: unknown;
    };
    const apiError = maybeAxios.response?.data?.error;
    if (typeof apiError === "string" && apiError.trim()) {
      return apiError;
    }
    const apiMessage = maybeAxios.response?.data?.message;
    if (typeof apiMessage === "string" && apiMessage.trim()) {
      return apiMessage;
    }
    if (typeof maybeAxios.message === "string" && maybeAxios.message.trim()) {
      return maybeAxios.message;
    }
  }
  return "Unable to create goal";
}

const schema = z.object({
  title: z.string().trim().min(3, "Title must be at least 3 characters"),
  description: z.string().optional(),
  weightage: z.number().min(1, "Weightage must be at least 1").max(100, "Weightage cannot exceed 100"),
  progress: z.number().min(0, "Progress cannot be negative").max(100, "Progress cannot exceed 100"),
  framework: z.enum(["OKR", "MBO", "Hybrid"]),
});

type FormValues = z.infer<typeof schema>;

export default function GoalsPage() {
  const { goals, loading, fetchGoals, addGoal, submitGoal, requestApproval, withdrawGoal } = useGoalsStore();
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const isManagerMode = activeMode === "manager";
  const isEmployee = user?.role === "employee";
  const canCreateGoals = Boolean(user && (user.role === "employee" || (user.role === "manager" && isManagerMode)));
  const canGenerateAiGoals = Boolean(user && (isEmployee || (user.role === "manager" && isManagerMode)));
  const [aiGoals, setAiGoals] = useState<AIGeneratedGoal[]>([]);
  const [aiContext, setAiContext] = useState<{ title: string; department: string; teamSize: number; focusArea: string } | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [managerCascadeGoals, setManagerCascadeGoals] = useState<CascadedManagerGoal[]>([]);
  const [employeeCascadeGoals, setEmployeeCascadeGoals] = useState<CascadedEmployeeGoal[]>([]);
  const [teamMembers, setTeamMembers] = useState<ManagerTeamMember[]>([]);
  const [selectedManagerCascadeGoalId, setSelectedManagerCascadeGoalId] = useState<string>("");
  const [cascadeDraft, setCascadeDraft] = useState<Record<string, { employee_id: string; target_value: number; target_percentage: number }>>({});
  const [aiSplitSuggestions, setAiSplitSuggestions] = useState<EmployeeCascadeSuggestion[]>([]);
  const [lineageByGoal, setLineageByGoal] = useState<Record<string, GoalLineageImpact>>({});
  const [selfGoalSummary, setSelfGoalSummary] = useState<SelfGoalSummary | null>(null);
  const [managerPendingGoals, setManagerPendingGoals] = useState<ManagerPendingGoal[]>([]);
  const [managerComments, setManagerComments] = useState<Record<string, string>>({});
  const [showCreateForm, setShowCreateForm] = useState(false);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", description: "", weightage: 25, progress: 0, framework: "OKR" },
  });

  useEffect(() => {
    fetchGoals().catch(() => null);
  }, [fetchGoals]);

  useEffect(() => {
    if (!user) {
      setManagerCascadeGoals([]);
      setEmployeeCascadeGoals([]);
      setTeamMembers([]);
      return;
    }

    if (isManagerMode) {
      Promise.all([
        leadershipGoalsService.listManagerCascadedGoals(),
        managerService.getTeam({ silent: true }),
        goalsService.getManagerPendingGoals(),
      ])
        .then(([goalsData, team, pending]) => {
          setManagerCascadeGoals(goalsData);
          setTeamMembers(team);
          setManagerPendingGoals(pending);
          if (goalsData.length > 0) {
            setSelectedManagerCascadeGoalId((previous) => previous || goalsData[0].goal_id);
          }
        })
        .catch(() => null);
      return;
    }

    if (isEmployee) {
      Promise.all([leadershipGoalsService.listEmployeeCascadedGoals(), goalsService.getSelfGoalSummary()])
        .then(([goalsData, summary]) => {
          setEmployeeCascadeGoals(goalsData);
          setSelfGoalSummary(summary);
        })
        .catch(() => null);
    }
  }, [user, isManagerMode, isEmployee]);

  const onSubmit = async (values: FormValues) => {
    try {
      if (isEmployee) {
        await goalsService.selfCreateGoal({
          title: values.title,
          description: values.description,
          weightage: values.weightage,
          framework: values.framework,
        });
        await fetchGoals();
        setSelfGoalSummary(await goalsService.getSelfGoalSummary());
      } else {
        await addGoal(values);
      }
      toast.success("Goal created");
      form.reset({ title: "", description: "", weightage: 25, progress: 0, framework: "OKR" });
      setShowCreateForm(false);
    } catch (error: unknown) {
      toast.error(extractErrorMessage(error));
    }
  };

  const onInvalid = (errors: FieldErrors<FormValues>) => {
    const firstError = Object.values(errors)[0];
    const message = firstError?.message;
    toast.error(typeof message === "string" ? message : "Please fix form validation errors before creating the goal");
  };

  const generateAIGoals = async () => {
    if (!user?.id) {
      toast.error("Please sign in to generate AI goals");
      return;
    }

    setAiLoading(true);
    try {
      const response = await aiService.generateGoalsForUser({ user_id: user.id });
      setAiGoals(response.goals || []);
      setAiContext({
        title: response.title,
        department: response.department,
        teamSize: response.team_size,
        focusArea: response.focus_area,
      });
      toast.success("AI goals generated based on role and team context");
    } catch {
      toast.error("Unable to generate AI goals");
    } finally {
      setAiLoading(false);
    }
  };

  const updateAIGoal = (index: number, field: keyof AIGeneratedGoal, value: string | number) => {
    setAiGoals((prev) => prev.map((goal, idx) => (idx === index ? { ...goal, [field]: value } : goal)));
  };

  const createGoalFromSuggestion = async (goal: AIGeneratedGoal) => {
    await addGoal({
      title: goal.title,
      description: `${goal.description}\n\nKPI: ${goal.kpi}`,
      weightage: goal.weightage,
      progress: 0,
      framework: "OKR",
    });
    toast.success("AI goal added to your goals");
  };

  const updateCascadeDraft = (employeeId: string, patch: Partial<{ target_value: number; target_percentage: number }>) => {
    setCascadeDraft((prev) => {
      const current = prev[employeeId] ?? { employee_id: employeeId, target_value: 0, target_percentage: 0 };
      return {
        ...prev,
        [employeeId]: {
          ...current,
          ...patch,
        },
      };
    });
  };

  const acknowledgeManagerCascadeGoal = async (goalId: string) => {
    try {
      const response = await leadershipGoalsService.acknowledgeManagerGoal(goalId);
      if (!response.acknowledged) {
        toast.error(response.reason || "Unable to acknowledge goal");
        return;
      }
      toast.success("Leadership cascaded goal acknowledged");
      const refreshed = await leadershipGoalsService.listManagerCascadedGoals();
      setManagerCascadeGoals(refreshed);
    } catch {
      toast.error("Unable to acknowledge cascaded goal");
    }
  };

  const suggestEmployeeSplit = async () => {
    const selected = managerCascadeGoals.find((goal) => goal.goal_id === selectedManagerCascadeGoalId);
    if (!selected) {
      toast.error("Select a cascaded goal first");
      return;
    }

    try {
      const response = await aiService.suggestEmployeeSplit({
        manager_name: user?.name || "Manager",
        total_target_value: Number(selected.target_value || 0),
        target_unit: selected.target_unit || "units",
        target_metric: selected.title,
        employees: teamMembers.map((member) => ({
          employee_id: member.id,
          name: member.name,
          role: member.role,
          current_workload_percentage: member.current_workload,
          historical_performance_score: member.avg_final_rating,
        })),
      });
      setAiSplitSuggestions(response.assignments);

      const suggestedDraft: Record<string, { employee_id: string; target_value: number; target_percentage: number }> = {};
      for (const row of response.assignments) {
        suggestedDraft[row.employee_id] = {
          employee_id: row.employee_id,
          target_value: Number(row.suggested_value.toFixed(2)),
          target_percentage: Number(row.suggested_percentage.toFixed(2)),
        };
      }
      setCascadeDraft(suggestedDraft);
      toast.success("AI split applied to team cascade draft");
    } catch {
      toast.error("Unable to generate employee split");
    }
  };

  const cascadeToTeam = async () => {
    if (!selectedManagerCascadeGoalId) {
      toast.error("Choose a manager cascaded goal first");
      return;
    }
    const payload = Object.values(cascadeDraft).filter((item) => item.target_percentage > 0 || item.target_value > 0);
    if (payload.length === 0) {
      toast.error("Set at least one employee target");
      return;
    }

    try {
      const response = await leadershipGoalsService.cascadeManagerGoalToTeam(selectedManagerCascadeGoalId, {
        employee_assignments: payload,
      });
      if (response.reason) {
        toast.error(response.reason);
        return;
      }
      toast.success(`Cascaded to ${response.count} team goals`);
      setCascadeDraft({});
      setAiSplitSuggestions([]);
    } catch {
      toast.error("Unable to cascade goal to team");
    }
  };

  const acknowledgeEmployeeGoal = async (goalId: string) => {
    try {
      await leadershipGoalsService.acknowledgeEmployeeGoal(goalId);
      toast.success("Goal acknowledged");
    } catch {
      toast.error("Unable to acknowledge goal");
    }
  };

  const loadLineage = async (goalId: string) => {
    if (lineageByGoal[goalId]) {
      return;
    }
    try {
      const payload = await leadershipGoalsService.getEmployeeLineage(goalId);
      setLineageByGoal((prev) => ({ ...prev, [goalId]: payload }));
    } catch {
      toast.error("Unable to load lineage impact");
    }
  };

  const handleRequestApproval = async (goalId: string) => {
    try {
      await requestApproval(goalId);
      if (isEmployee) {
        setSelfGoalSummary(await goalsService.getSelfGoalSummary());
      }
      toast.success("Goal sent for manager approval");
    } catch {
      toast.error("Unable to request approval");
    }
  };

  const handleWithdrawGoal = async (goalId: string) => {
    try {
      await withdrawGoal(goalId);
      if (isEmployee) {
        setSelfGoalSummary(await goalsService.getSelfGoalSummary());
      }
      toast.success("Approval request withdrawn");
    } catch {
      toast.error("Unable to withdraw goal");
    }
  };

  const handleManagerDecision = async (goalId: string, action: "approve" | "request-edit" | "reject") => {
    const comment = managerComments[goalId]?.trim();
    try {
      if (action === "approve") {
        await goalsService.managerApproveGoal(goalId, comment);
      } else if (action === "request-edit") {
        await goalsService.managerRequestEdit(goalId, comment);
      } else {
        await goalsService.managerRejectGoal(goalId, comment);
      }

      const pending = await goalsService.getManagerPendingGoals();
      await fetchGoals();
      setManagerPendingGoals(pending);
      setManagerComments((prev) => ({ ...prev, [goalId]: "" }));
      toast.success("Decision saved");
    } catch {
      toast.error("Unable to save manager decision");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title={isManagerMode ? "Team Goals" : "My Goals"}
        description={
          isManagerMode
            ? "Review direct-report goals and approve submitted plans."
            : "Plan measurable outcomes, track progress, and submit goals for approval."
        }
        action={
          <div className="flex items-center gap-2">
            {canCreateGoals && (
              <>
                {canGenerateAiGoals ? (
                  <Button variant="outline" onClick={generateAIGoals} disabled={aiLoading}>
                    <Sparkles className="mr-2 h-4 w-4" />
                    {aiLoading ? "Generating..." : isEmployee ? "Suggest Goals" : "Generate AI Goals"}
                  </Button>
                ) : null}
                <Button onClick={() => setShowCreateForm(!showCreateForm)}>
                  {showCreateForm ? "Cancel" : "New Goal"}
                </Button>
              </>
            )}
          </div>
        }
      />

      <SectionContainer columns="dashboard">
        {isEmployee && selfGoalSummary ? (
          <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 xl:col-span-12">
            <CardTitle>Self-Created Goal Tracker</CardTitle>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-border/70 p-3">
                <p className="text-xs text-muted-foreground">Total Weightage</p>
                <p className="text-lg font-semibold text-foreground">{selfGoalSummary.total_weightage.toFixed(1)}%</p>
              </div>
              <div className="rounded-xl border border-border/70 p-3">
                <p className="text-xs text-muted-foreground">Pending Approval</p>
                <p className="text-lg font-semibold text-warning">{selfGoalSummary.pending_approval_count}</p>
              </div>
              <div className="rounded-xl border border-border/70 p-3">
                <p className="text-xs text-muted-foreground">Edit Requested</p>
                <p className="text-lg font-semibold text-info">{selfGoalSummary.edit_requested_count}</p>
              </div>
              <div className="rounded-xl border border-border/70 p-3">
                <p className="text-xs text-muted-foreground">Approved</p>
                <p className="text-lg font-semibold text-success">{selfGoalSummary.approved_count}</p>
              </div>
            </div>
          </Card>
        ) : null}

        {canGenerateAiGoals && aiGoals.length > 0 ? (
          <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-12">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" /> Role-based Goal Suggestions
            </div>
            <CardTitle>AI Goal Drafts</CardTitle>
            <CardDescription>
              {aiContext
                ? `${aiContext.title} in ${aiContext.department} | Team size: ${aiContext.teamSize} | Focus: ${aiContext.focusArea}`
                : "Edit suggestions, then add them to your goal plan."}
            </CardDescription>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {aiGoals.map((goal, idx) => (
                <div key={`${goal.title}-${idx}`} className="space-y-3 rounded-xl border border-border bg-background/60 p-4">
                  <Input value={goal.title} onChange={(event) => updateAIGoal(idx, "title", event.target.value)} />
                  <Textarea value={goal.description} onChange={(event) => updateAIGoal(idx, "description", event.target.value)} />
                  <Input value={goal.kpi} onChange={(event) => updateAIGoal(idx, "kpi", event.target.value)} placeholder="KPI" />
                  <Input
                    type="number"
                    value={goal.weightage}
                    onChange={(event) => updateAIGoal(idx, "weightage", Number(event.target.value))}
                    min={1}
                    max={100}
                  />
                  <Button className="w-full" variant="secondary" onClick={() => createGoalFromSuggestion(goal)}>
                    Add as Goal
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {canCreateGoals && showCreateForm && (
        <Card id="create-goal-form" className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
          <div className="flex items-center justify-between gap-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Target className="h-3.5 w-3.5" /> Goal Planning
            </div>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="rounded-lg p-1.5 hover:bg-secondary/60 transition-colors"
              aria-label="Close form"
            >
              <X className="h-5 w-5 text-muted-foreground" />
            </button>
          </div>
          <CardTitle>Create Goal</CardTitle>
          <CardDescription>Define measurable outcomes and assign framework, progress, and weightage.</CardDescription>
          <form onSubmit={form.handleSubmit(onSubmit, onInvalid)} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Goal Title</label>
              <Input placeholder="Improve release quality" {...form.register("title")} />
              {form.formState.errors.title && (
                <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Description</label>
              <Textarea placeholder="Define scope and success criteria" {...form.register("description")} />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Weightage (%)</label>
                <Input type="number" placeholder="25" {...form.register("weightage", { valueAsNumber: true })} />
                {form.formState.errors.weightage && (
                  <p className="text-xs text-destructive">{form.formState.errors.weightage.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Progress (%)</label>
                <Input type="number" placeholder="0" {...form.register("progress", { valueAsNumber: true })} />
                {form.formState.errors.progress && (
                  <p className="text-xs text-destructive">{form.formState.errors.progress.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Framework</label>
              <select
                className="h-10 w-full rounded-lg border border-input bg-card px-3 text-sm text-foreground focus:border-primary/55 focus:outline-none focus:ring-2 focus:ring-primary/30"
                {...form.register("framework")}
              >
                <option value="OKR">OKR</option>
                <option value="MBO">MBO</option>
                <option value="Hybrid">Hybrid</option>
              </select>
              {form.formState.errors.framework && (
                <p className="text-xs text-destructive">{form.formState.errors.framework.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full">Create Goal</Button>
          </form>
        </Card>
        )}

        <div className={`space-y-6 ${isManagerMode ? "xl:col-span-12" : "xl:col-span-8"}`}>
          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>{isManagerMode ? `Team Goals (${goals.length})` : `My Goals (${goals.length})`}</CardTitle>
            <CardDescription>
              {isManagerMode
                ? "Direct-report and manager goals are shown for team review and approvals."
                : "Manager-assigned and self-created goals are listed below with their Goal ID for meeting creation."}
            </CardDescription>
          </Card>

          {isManagerMode ? (
            <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Pending Self-Created Goal Approvals</CardTitle>
              <CardDescription>Review employee-submitted self-created goals and approve, request edits, or reject with comments.</CardDescription>

              {managerPendingGoals.length === 0 ? <p className="text-sm text-muted-foreground">No pending self-created goals.</p> : null}

              {managerPendingGoals.map((item) => (
                <div key={item.goal.id} className="space-y-3 rounded-xl border border-border/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{item.goal.title}</p>
                      <p className="text-xs text-muted-foreground">{item.employee_name} ({item.employee_role}) | {item.employee_department || "General"}</p>
                    </div>
                    <Badge>{item.goal.weightage}%</Badge>
                  </div>
                  {item.goal.description ? <p className="text-xs text-muted-foreground">{item.goal.description}</p> : null}
                  {item.goal.ai_assessment && typeof item.goal.ai_assessment["quality_score"] === "number" ? (
                    <p className="text-xs text-muted-foreground">AI assessment score: {(Number(item.goal.ai_assessment["quality_score"]) * 100).toFixed(0)}%</p>
                  ) : null}
                  <Textarea
                    placeholder="Add comment for employee"
                    value={managerComments[item.goal.id] || ""}
                    onChange={(event) => setManagerComments((prev) => ({ ...prev, [item.goal.id]: event.target.value }))}
                  />
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={() => handleManagerDecision(item.goal.id, "approve")}>Approve</Button>
                    <Button size="sm" variant="secondary" onClick={() => handleManagerDecision(item.goal.id, "request-edit")}>Request Edit</Button>
                    <Button size="sm" variant="outline" onClick={() => handleManagerDecision(item.goal.id, "reject")}>Reject</Button>
                  </div>
                </div>
              ))}
            </Card>
          ) : null}

          {isManagerMode ? (
            <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>Leadership Cascaded Goals</CardTitle>
                  <CardDescription>Acknowledge leadership goals, then split each target into employee-level contributions.</CardDescription>
                </div>
                <Button variant="outline" onClick={suggestEmployeeSplit} disabled={!selectedManagerCascadeGoalId || teamMembers.length === 0}>
                  <Sparkles className="mr-2 h-4 w-4" /> Suggest Employee Split
                </Button>
              </div>

              <div className="space-y-3">
                {managerCascadeGoals.length === 0 ? <p className="text-sm text-muted-foreground">No leadership cascaded goals assigned yet.</p> : null}
                {managerCascadeGoals.map((goal) => (
                  <div key={goal.goal_id} className="rounded-xl border border-border/70 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedManagerCascadeGoalId(goal.goal_id)}
                        className="text-left text-sm font-semibold text-foreground"
                      >
                        {goal.title}
                      </button>
                      <div className="flex items-center gap-2">
                        <Badge>{goal.target_value || 0} {goal.target_unit || "units"}</Badge>
                        <Button size="sm" variant="outline" onClick={() => acknowledgeManagerCascadeGoal(goal.goal_id)}>Acknowledge</Button>
                      </div>
                    </div>
                    {goal.description ? <p className="mt-2 text-xs text-muted-foreground">{goal.description}</p> : null}
                  </div>
                ))}
              </div>

              {selectedManagerCascadeGoalId ? (
                <div className="space-y-3 rounded-xl border border-border/70 p-4">
                  <p className="text-sm font-semibold text-foreground">Cascade to Team</p>
                  {teamMembers.map((member) => {
                    const draft = cascadeDraft[member.id] ?? { employee_id: member.id, target_value: 0, target_percentage: 0 };
                    return (
                      <div key={member.id} className="grid grid-cols-1 gap-2 md:grid-cols-[1.2fr_1fr_1fr]">
                        <div>
                          <p className="text-sm font-medium text-foreground">{member.name}</p>
                          <p className="text-xs text-muted-foreground">{member.role} | Workload {member.current_workload.toFixed(1)}%</p>
                        </div>
                        <Input
                          type="number"
                          placeholder="Target value"
                          value={draft.target_value}
                          onChange={(event) => updateCascadeDraft(member.id, { target_value: Number(event.target.value) || 0 })}
                        />
                        <Input
                          type="number"
                          placeholder="Target %"
                          value={draft.target_percentage}
                          onChange={(event) => updateCascadeDraft(member.id, { target_percentage: Number(event.target.value) || 0 })}
                        />
                      </div>
                    );
                  })}
                  <Button onClick={cascadeToTeam}>Cascade to Team</Button>
                </div>
              ) : null}

              {aiSplitSuggestions.length > 0 ? (
                <div className="space-y-2 rounded-xl border border-border/70 p-4">
                  <p className="text-sm font-semibold text-foreground">AI Suggested Split Rationale</p>
                  {aiSplitSuggestions.map((item) => {
                    const member = teamMembers.find((entry) => entry.id === item.employee_id);
                    return (
                      <p key={item.employee_id} className="text-xs text-muted-foreground">
                        {(member?.name || "Employee")}: {item.suggested_percentage.toFixed(1)}% ({item.suggested_value.toFixed(2)}) - {item.rationale}
                      </p>
                    );
                  })}
                </div>
              ) : null}
            </Card>
          ) : null}

          {isEmployee ? (
            <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Cascaded Goals from Manager</CardTitle>
              <CardDescription>Acknowledge assigned cascaded goals and inspect lineage impact on your manager and leadership target.</CardDescription>

              {employeeCascadeGoals.length === 0 ? <p className="text-sm text-muted-foreground">No cascaded goals assigned by your manager yet.</p> : null}

              {employeeCascadeGoals.map((goal) => {
                const lineage = lineageByGoal[goal.goal_id];
                return (
                  <div key={goal.goal_id} className="space-y-3 rounded-xl border border-border/70 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-foreground">{goal.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {goal.target_value || 0} {goal.target_unit || "units"} | {goal.target_percentage?.toFixed(1) || 0}% contribution
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {goal.contribution_level ? <Badge>{goal.contribution_level}</Badge> : null}
                        <Button size="sm" variant="outline" onClick={() => acknowledgeEmployeeGoal(goal.goal_id)}>Acknowledge</Button>
                        <Button size="sm" variant="secondary" onClick={() => loadLineage(goal.goal_id)}>View Impact</Button>
                      </div>
                    </div>

                    {lineage ? (
                      <div className="rounded-lg border border-border/70 p-3">
                        <p className="text-xs text-muted-foreground">Manager Goal: {lineage.manager_title || "Not linked"}</p>
                        <p className="text-xs text-muted-foreground">AOP Target: {lineage.aop_title || "Not linked"}</p>
                        <p className="mt-2 text-xs text-muted-foreground">{lineage.business_context || "No business context available."}</p>
                        {typeof lineage.manager_progress === "number" ? (
                          <div className="mt-3 space-y-2">
                            <p className="text-xs text-foreground">Manager Progress {lineage.manager_progress.toFixed(1)}%</p>
                            <Progress value={lineage.manager_progress} />
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </Card>
          ) : null}

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {loading
              ? Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-48" />)
              : goals.length === 0
                ? <Card className="md:col-span-2"><CardDescription>No goals yet. Create one to see it here.</CardDescription></Card>
              : goals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    onSubmit={(id) => submitGoal(id).then(() => toast.success("Goal submitted"))}
                    onRequestApproval={isEmployee ? handleRequestApproval : undefined}
                    onWithdraw={isEmployee ? handleWithdrawGoal : undefined}
                  />
                ))}
          </div>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Goal Timeline</CardTitle>
            <div className="mt-4">
              <GoalTimeline />
            </div>
          </Card>
        </div>
      </SectionContainer>
    </motion.div>
  );
}

