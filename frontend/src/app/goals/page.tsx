"use client";

import { useEffect } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { GoalCard } from "@/components/goals/GoalCard";
import { GoalTimeline } from "@/components/goals/GoalTimeline";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { Skeleton } from "@/components/ui/skeleton";
import { useGoalsStore } from "@/store/useGoalsStore";
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

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Goals"
        description="Plan measurable outcomes, track progress, and submit goals for approval."
        action={
          <Button onClick={() => document.getElementById("create-goal-form")?.scrollIntoView({ behavior: "smooth", block: "start" })}>
            New Goal
          </Button>
        }
      />

      <SectionContainer columns="dashboard">
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

        <div className="space-y-6 xl:col-span-8">
          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Goal Timeline</CardTitle>
            <div className="mt-4">
              <GoalTimeline />
            </div>
          </Card>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>My Goals ({goals.length})</CardTitle>
            <CardDescription>
              Created goals are listed below with their Goal ID for meeting creation.
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
