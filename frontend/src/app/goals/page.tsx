"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
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
import { Skeleton } from "@/components/ui/skeleton";
import { useGoalsStore } from "@/store/useGoalsStore";
import { toast } from "sonner";

const schema = z.object({
  title: z.string().min(3),
  description: z.string().optional(),
  weightage: z.number().min(1).max(100),
  progress: z.number().min(0).max(100),
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
    await addGoal(values);
    toast.success("Goal created");
    form.reset({ title: "", description: "", weightage: 25, progress: 0, framework: "OKR" });
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <PageHeader
        title="Goals"
        description="Plan measurable outcomes, track progress, and submit goals for approval."
        action={
          <Button onClick={() => document.getElementById("create-goal-form")?.scrollIntoView({ behavior: "smooth", block: "start" })}>
            New Goal
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <Card id="create-goal-form" className="space-y-4 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Target className="h-3.5 w-3.5" /> Goal Planning
          </div>
          <CardTitle>Create Goal</CardTitle>
          <CardDescription>Define measurable outcomes and assign framework, progress, and weightage.</CardDescription>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Goal Title</label>
              <Input placeholder="Improve release quality" {...form.register("title")} />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Description</label>
              <Textarea placeholder="Define scope and success criteria" {...form.register("description")} />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Weightage (%)</label>
                <Input type="number" placeholder="25" {...form.register("weightage", { valueAsNumber: true })} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Progress (%)</label>
                <Input type="number" placeholder="0" {...form.register("progress", { valueAsNumber: true })} />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Framework</label>
              <select
                className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground focus:border-primary/55 focus:outline-none focus:ring-2 focus:ring-primary/30"
                {...form.register("framework")}
              >
                <option value="OKR">OKR</option>
                <option value="MBO">MBO</option>
                <option value="Hybrid">Hybrid</option>
              </select>
            </div>

            <Button type="submit" className="w-full">Create Goal</Button>
          </form>
        </Card>

        <div className="space-y-6 xl:col-span-8">
          <Card>
            <CardTitle>Goal Timeline</CardTitle>
            <div className="mt-4">
              <GoalTimeline />
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {loading
              ? Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-48" />)
              : goals.map((goal) => (
                  <GoalCard key={goal.id} goal={goal} onSubmit={(id) => submitGoal(id).then(() => toast.success("Goal submitted"))} />
                ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
