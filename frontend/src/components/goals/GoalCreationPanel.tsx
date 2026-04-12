"use client";

import { FieldErrors, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Target, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const schema = z.object({
  title: z.string().trim().min(3, "Title must be at least 3 characters"),
  description: z.string().optional(),
  weightage: z.number().min(1, "Weightage must be at least 1").max(100, "Weightage cannot exceed 100"),
  progress: z.number().min(0, "Progress cannot be negative").max(100, "Progress cannot exceed 100"),
  framework: z.enum(["OKR", "MBO", "Hybrid"]),
});

export type CreateGoalInput = z.infer<typeof schema>;

interface GoalCreationPanelProps {
  onSubmitGoal: (values: CreateGoalInput) => Promise<void>;
  onClose: () => void;
}

export function GoalCreationPanel({ onSubmitGoal, onClose }: GoalCreationPanelProps) {
  const form = useForm<CreateGoalInput>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", description: "", weightage: 25, progress: 0, framework: "OKR" },
  });

  const onInvalid = (errors: FieldErrors<CreateGoalInput>) => {
    const firstError = Object.values(errors)[0];
    const message = firstError?.message;
    toast.error(typeof message === "string" ? message : "Please fix form validation errors before creating the goal");
  };

  const onSubmit = async (values: CreateGoalInput) => {
    await onSubmitGoal(values);
    form.reset({ title: "", description: "", weightage: 25, progress: 0, framework: "OKR" });
  };

  return (
    <Card id="create-goal-form" className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
      <div className="flex items-center justify-between gap-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <Target className="h-3.5 w-3.5" /> Goal Planning
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 transition-colors hover:bg-secondary/60"
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
          {form.formState.errors.title && <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Description</label>
          <Textarea placeholder="Define scope and success criteria" {...form.register("description")} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Weightage (%)</label>
            <Input type="number" placeholder="25" {...form.register("weightage", { valueAsNumber: true })} />
            {form.formState.errors.weightage && <p className="text-xs text-destructive">{form.formState.errors.weightage.message}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Progress (%)</label>
            <Input type="number" placeholder="0" {...form.register("progress", { valueAsNumber: true })} />
            {form.formState.errors.progress && <p className="text-xs text-destructive">{form.formState.errors.progress.message}</p>}
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
          {form.formState.errors.framework && <p className="text-xs text-destructive">{form.formState.errors.framework.message}</p>}
        </div>

        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating..." : "Create Goal"}
        </Button>
      </form>
    </Card>
  );
}