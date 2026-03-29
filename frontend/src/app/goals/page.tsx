"use client";

import { useEffect, useState } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Sparkles, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { GoalCard } from "@/components/goals/GoalCard";
import { GoalTimeline } from "@/components/goals/GoalTimeline";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { Skeleton } from "@/components/ui/skeleton";
import { aiService } from "@/services/ai";
import { useGoalsStore } from "@/store/useGoalsStore";
import { useSessionStore } from "@/store/useSessionStore";
import type { AIGeneratedGoal } from "@/types";
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
  const { goals, loading, fetchGoals, addGoal, submitGoal } = useGoalsStore();
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const isManagerMode = activeMode === "manager";
  const canManagerCreateGoals = Boolean(user && user.role === "manager" && isManagerMode);
  const [aiGoals, setAiGoals] = useState<AIGeneratedGoal[]>([]);
  const [aiContext, setAiContext] = useState<{ title: string; department: string; teamSize: number; focusArea: string } | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", description: "", weightage: 25, progress: 0, framework: "OKR" },
  });

  useEffect(() => {
    fetchGoals().catch(() => null);
  }, [fetchGoals]);

  const onSubmit = async (values: FormValues) => {
    try {
      await addGoal(values);
      toast.success("Goal created");
      form.reset({ title: "", description: "", weightage: 25, progress: 0, framework: "OKR" });
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
            {canManagerCreateGoals && (
              <>
                <Button variant="outline" onClick={generateAIGoals} disabled={aiLoading}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  {aiLoading ? "Generating..." : "Generate AI Goals"}
                </Button>
                <Button onClick={() => document.getElementById("create-goal-form")?.scrollIntoView({ behavior: "smooth", block: "start" })}>
                  New Goal
                </Button>
              </>
            )}
          </div>
        }
      />

      <SectionContainer columns="dashboard">
        {canManagerCreateGoals && aiGoals.length > 0 ? (
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

        {canManagerCreateGoals && (
        <Card id="create-goal-form" className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Target className="h-3.5 w-3.5" /> Goal Planning
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
            <CardTitle>Goal Timeline</CardTitle>
            <div className="mt-4">
              <GoalTimeline />
            </div>
          </Card>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>{isManagerMode ? `Team Goals (${goals.length})` : `My Goals (${goals.length})`}</CardTitle>
            <CardDescription>
              {isManagerMode
                ? "Direct-report and manager goals are shown for team review and approvals."
                : "Created goals are listed below with their Goal ID for meeting creation."}
            </CardDescription>
          </Card>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {loading
              ? Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-48" />)
              : goals.length === 0
                ? <Card className="md:col-span-2"><CardDescription>No goals yet. Create one to see it here.</CardDescription></Card>
              : goals.map((goal) => (
                  <GoalCard key={goal.id} goal={goal} onSubmit={(id) => submitGoal(id).then(() => toast.success("Goal submitted"))} />
                ))}
          </div>
        </div>
      </SectionContainer>
    </motion.div>
  );
}
