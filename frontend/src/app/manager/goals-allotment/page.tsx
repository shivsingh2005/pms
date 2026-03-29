"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useSessionStore } from "@/store/useSessionStore";
import { managerService } from "@/services/manager";
import { aiService } from "@/services/ai";
import { goalsService } from "@/services/goals";
import type { AIGeneratedGoal, ManagerTeamMember } from "@/types";

export default function ManagerGoalsAllotmentPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const setActiveMode = useSessionStore((s) => s.setActiveMode);

  const [team, setTeam] = useState<ManagerTeamMember[]>([]);
  const [loadingTeam, setLoadingTeam] = useState(false);
  const [objective, setObjective] = useState("");
  const [generating, setGenerating] = useState(false);
  const [employeeGoals, setEmployeeGoals] = useState<Record<string, AIGeneratedGoal[]>>({});
  const [assigningEmployeeId, setAssigningEmployeeId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, router, setActiveMode, user]);

  const loadTeam = async () => {
    setLoadingTeam(true);
    try {
      const items = await managerService.getTeam();
      setTeam(items);
    } catch {
      toast.error("Failed to load manager team");
    } finally {
      setLoadingTeam(false);
    }
  };

  useEffect(() => {
    if (!user || activeMode !== "manager") return;
    loadTeam().catch(() => null);
  }, [activeMode, user]);

  const generateTeamGoals = async () => {
    if (!user) return;
    setGenerating(true);
    try {
      const payload = await aiService.generateTeamGoals({
        manager_id: user.id,
        organization_objectives: objective.trim() || undefined,
      });
      const map: Record<string, AIGeneratedGoal[]> = {};
      for (const row of payload.employees) {
        map[row.employee_id] = row.goals;
      }
      setEmployeeGoals(map);
      toast.success("AI generated team goals");
    } catch {
      toast.error("Unable to generate team goals");
    } finally {
      setGenerating(false);
    }
  };

  const projectedWorkload = (member: ManagerTeamMember) => {
    const generated = employeeGoals[member.id] ?? [];
    const added = generated.reduce((sum, goal) => sum + (Number(goal.weightage) || 0), 0);
    return Math.round((member.current_workload + added) * 10) / 10;
  };

  const updateGoal = (employeeId: string, index: number, field: keyof AIGeneratedGoal, value: string | number) => {
    setEmployeeGoals((prev) => {
      const copy = { ...prev };
      copy[employeeId] = [...(copy[employeeId] ?? [])];
      copy[employeeId][index] = { ...copy[employeeId][index], [field]: value };
      return copy;
    });
  };

  const addGoal = (employeeId: string) => {
    setEmployeeGoals((prev) => ({
      ...prev,
      [employeeId]: [
        ...(prev[employeeId] ?? []),
        { title: "", description: "", kpi: "", weightage: 20 },
      ],
    }));
  };

  const removeGoal = (employeeId: string, index: number) => {
    setEmployeeGoals((prev) => ({
      ...prev,
      [employeeId]: (prev[employeeId] ?? []).filter((_, idx) => idx !== index),
    }));
  };

  const assignGoals = async (employeeId: string, action: "approve" | "draft" | "reject") => {
    const goals = employeeGoals[employeeId] ?? [];
    if (goals.length === 0) {
      toast.error("No goals available for this employee");
      return;
    }

    setAssigningEmployeeId(employeeId);
    try {
      await goalsService.assignGoals({
        employee_id: employeeId,
        approve: action === "approve",
        reject: action === "reject",
        is_ai_generated: true,
        goals: goals.map((goal) => ({
          title: goal.title,
          description: goal.description,
          kpi: goal.kpi,
          weightage: Number(goal.weightage) || 0,
          framework: "OKR",
          progress: 0,
        })),
      });
      toast.success(action === "approve" ? "Goals approved and assigned" : action === "reject" ? "Goals rejected" : "Goals saved as draft");
      await loadTeam();
    } catch {
      toast.error("Failed to assign goals");
    } finally {
      setAssigningEmployeeId(null);
    }
  };

  const teamCards = team.map((member) => {
    const generated = employeeGoals[member.id] ?? [];
    const projected = projectedWorkload(member);
    const overloaded = projected > 100 || member.current_workload > 100;

    return (
      <Card key={member.id} className="rounded-xl p-5 border bg-card space-y-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle>{member.name}</CardTitle>
            <CardDescription>{member.role} · {member.department}</CardDescription>
          </div>
          <Link href={`/manager/employee/${member.id}`}>
            <Button variant="outline" size="sm">Inspect</Button>
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg border border-border/70 p-2">
            <p className="text-muted-foreground">Current workload</p>
            <p className="font-semibold">{member.current_workload}%</p>
          </div>
          <div className="rounded-lg border border-border/70 p-2">
            <p className="text-muted-foreground">Current goals</p>
            <p className="font-semibold">{member.current_goals_count}</p>
          </div>
        </div>

        {overloaded && (
          <p className="rounded-md border border-warning/40 bg-warning/15 px-3 py-2 text-xs text-warning">
            Employee overloaded. Current/projected workload is above 100%.
          </p>
        )}

        <p className="text-xs text-muted-foreground">Projected workload after assignment: {projected}%</p>

        <div className="space-y-3">
          {(generated.length > 0 ? generated : []).map((goal, idx) => (
            <div key={`${member.id}-${idx}`} className="space-y-2 rounded-lg border border-border/70 p-3">
              <Input value={goal.title} onChange={(e) => updateGoal(member.id, idx, "title", e.target.value)} placeholder="Goal title" />
              <Textarea value={goal.description} onChange={(e) => updateGoal(member.id, idx, "description", e.target.value)} placeholder="Description" />
              <Input value={goal.kpi} onChange={(e) => updateGoal(member.id, idx, "kpi", e.target.value)} placeholder="KPI" />
              <Input
                type="number"
                value={goal.weightage}
                onChange={(e) => updateGoal(member.id, idx, "weightage", Number(e.target.value))}
                min={0}
                max={100}
              />
              <Button variant="ghost" size="sm" onClick={() => removeGoal(member.id, idx)}>Remove goal</Button>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => addGoal(member.id)}>Add Goal</Button>
          <Button size="sm" onClick={() => assignGoals(member.id, "approve")} disabled={assigningEmployeeId === member.id}>Approve</Button>
          <Button variant="secondary" size="sm" onClick={() => assignGoals(member.id, "draft")} disabled={assigningEmployeeId === member.id}>Save Draft</Button>
          <Button variant="destructive" size="sm" onClick={() => assignGoals(member.id, "reject")} disabled={assigningEmployeeId === member.id}>Reject</Button>
        </div>
      </Card>
    );
  });

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Manager Goal Allotment Window"
        description="Generate team goals with AI, edit allocations, and approve or reject assignments."
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => loadTeam().catch(() => null)} disabled={loadingTeam}>Refresh Team</Button>
            <Button onClick={generateTeamGoals} disabled={generating || loadingTeam}>
              <Sparkles className="mr-2 h-4 w-4" />
              {generating ? "Generating..." : "Generate Team Goals with AI"}
            </Button>
          </div>
        }
      />

      <Card className="rounded-xl p-5 border bg-card space-y-3">
        <CardTitle>AI Context</CardTitle>
        <CardDescription>Provide optional organizational objectives for better team-level goal distribution.</CardDescription>
        <Textarea value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Example: Improve release quality and reduce incident response time." />
      </Card>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {teamCards}
      </section>
    </motion.div>
  );
}
