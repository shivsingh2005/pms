"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Target } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { aiService } from "@/services/ai";
import { employeeService } from "@/services/employee";
import { useSessionStore } from "@/store/useSessionStore";
import type { AIGrowthSuggestionResult, AIQuarterlyUsage, CycleTimelineState } from "@/types";

const EMPTY_GROWTH: AIGrowthSuggestionResult = {
  growth_suggestions: [],
  next_quarter_plan: [],
  recommended_training: [],
};

export default function EmployeeGrowthHubPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  const [skillsInput, setSkillsInput] = useState("communication, execution");
  const [targetRole, setTargetRole] = useState("Senior Individual Contributor");
  const [loading, setLoading] = useState(false);

  const [timelineState, setTimelineState] = useState<CycleTimelineState | null>(null);
  const [usage, setUsage] = useState<AIQuarterlyUsage | null>(null);
  const [growthPlan, setGrowthPlan] = useState<AIGrowthSuggestionResult>(EMPTY_GROWTH);

  const parsedSkills = useMemo(
    () => skillsInput.split(",").map((item) => item.trim()).filter(Boolean),
    [skillsInput],
  );

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (user.role !== "employee") {
      router.push("/unauthorized");
      return;
    }

    const load = async () => {
      try {
        const [timeline, usageData] = await Promise.all([
          employeeService.getCycleTimelineState(),
          aiService.getQuarterlyUsage(),
        ]);
        setTimelineState(timeline);
        setUsage(usageData);
      } catch {
        toast.error("Unable to load growth hub data");
      }
    };

    load().catch(() => null);
  }, [router, user]);

  const buildGrowthPlan = async () => {
    if (!user) {
      return;
    }

    if (parsedSkills.length === 0) {
      toast.error("Add at least one skill");
      return;
    }

    setLoading(true);
    try {
      const data = await aiService.growthSuggestion({
        role: user.role,
        department: user.department || "General",
        current_skills: parsedSkills,
        target_role: targetRole.trim() || "Next role",
      });
      setGrowthPlan(data);
      toast.success("Growth plan generated");
    } catch {
      toast.error("Failed to generate growth plan");
    } finally {
      setLoading(false);
    }
  };

  if (!user || user.role !== "employee") {
    return null;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Growth Hub"
        description="Track your cycle progress and generate AI-guided development suggestions."
        action={
          <Button onClick={buildGrowthPlan} disabled={loading}>
            <Sparkles className="mr-2 h-4 w-4" />
            {loading ? "Generating..." : "Generate Plan"}
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="space-y-3">
          <CardTitle className="inline-flex items-center gap-2">
            <Target className="h-4 w-4" />
            AI Development Plan
          </CardTitle>
          <CardDescription>Provide your current skills and next role aspiration.</CardDescription>

          <label className="space-y-1 text-sm">
            <span className="text-xs text-muted-foreground">Current skills (comma-separated)</span>
            <Input
              value={skillsInput}
              onChange={(event) => setSkillsInput(event.target.value)}
              placeholder="execution, stakeholder management, data analysis"
            />
          </label>

          <label className="space-y-1 text-sm">
            <span className="text-xs text-muted-foreground">Target role</span>
            <Input
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
              placeholder="Senior Engineer"
            />
          </label>

          <div className="space-y-2 rounded-lg border border-border/70 p-3">
            <p className="text-sm font-medium text-foreground">Growth suggestions</p>
            {(growthPlan.growth_suggestions.length > 0 ? growthPlan.growth_suggestions : ["Generate plan to view suggestions"]).map((item, index) => (
              <p key={`growth-suggestion-${index}`} className="text-xs text-muted-foreground">• {item}</p>
            ))}
          </div>

          <div className="space-y-2 rounded-lg border border-border/70 p-3">
            <p className="text-sm font-medium text-foreground">Next quarter plan</p>
            {(growthPlan.next_quarter_plan.length > 0 ? growthPlan.next_quarter_plan : ["Generate plan to view quarter plan"]).map((item, index) => (
              <p key={`growth-quarter-${index}`} className="text-xs text-muted-foreground">• {item}</p>
            ))}
          </div>

          <div className="space-y-2 rounded-lg border border-border/70 p-3">
            <p className="text-sm font-medium text-foreground">Recommended training</p>
            {(growthPlan.recommended_training.length > 0 ? growthPlan.recommended_training : ["Generate plan to view training suggestions"]).map((item, index) => (
              <p key={`growth-training-${index}`} className="text-xs text-muted-foreground">• {item}</p>
            ))}
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="space-y-3">
            <CardTitle>Cycle Timeline State</CardTitle>
            <CardDescription>Milestone visibility for your current performance cycle.</CardDescription>
            {timelineState?.items?.length ? (
              <div className="space-y-2">
                {timelineState.items.map((item) => (
                  <div key={item.id} className="rounded-lg border border-border/70 p-3">
                    <p className="text-sm font-medium text-foreground">{item.node_name}</p>
                    <p className="text-xs text-muted-foreground">Status: {item.status}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Timeline data unavailable.</p>
            )}
          </Card>

          <Card className="space-y-3">
            <CardTitle>AI Quarterly Usage</CardTitle>
            <CardDescription>
              Q{usage?.quarter ?? "-"} {usage?.year ?? "-"}
            </CardDescription>
            {usage?.features?.length ? (
              <div className="space-y-2">
                {usage.features.map((feature) => {
                  const usedPercent = Math.min((feature.used / Math.max(feature.limit, 1)) * 100, 100);
                  return (
                    <div key={feature.feature_name} className="rounded-lg border border-border/70 p-3">
                      <p className="text-sm font-medium text-foreground">{feature.feature_name.replaceAll("_", " ")}</p>
                      <p className="text-xs text-muted-foreground">{feature.used} / {feature.limit} used</p>
                      <div className="mt-2 h-2 w-full rounded bg-muted/70">
                        <div className="h-2 rounded bg-primary" style={{ width: `${usedPercent}%` }} />
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">Remaining: {feature.remaining}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Usage data unavailable.</p>
            )}
          </Card>
        </div>
      </div>
    </motion.div>
  );
}

