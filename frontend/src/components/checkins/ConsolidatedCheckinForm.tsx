"use client";

import React, { useState, useEffect } from "react";
import { useGoalsStore } from "@/store/useGoalsStore";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { checkinsService } from "@/services/checkins";
import { performanceCyclesService } from "@/services/performance-cycles";
import type { Goal } from "@/types";
import {
  AlertCircle,
  FileText,
  Zap,
  Upload,
} from "lucide-react";

interface GoalStatusUpdate {
  goalId: string;
  title: string;
  rag: "RED" | "AMBER" | "GREEN";
  progress: number;
}

const RAG_SEQUENCE: Record<GoalStatusUpdate["rag"], GoalStatusUpdate["rag"]> = {
  RED: "AMBER",
  AMBER: "GREEN",
  GREEN: "RED",
};

/**
 * Consolidated Check-in Form
 *
 * PRD FIX 9: One unified check-in covering ALL goals simultaneously.
 * Not per-goal check-ins — one submission for all approved goals.
 *
 * Features:
 * - Quick RAG status toggle per goal
 * - Consolidated overall update (3 fields max)
 * - Smart pre-filling from last check-in
 * - Final check-in toggle
 * - Shows remaining check-ins for quarter
 */
export function ConsolidatedCheckinForm() {
  const goals = useGoalsStore((state) => state.goals);
  const fetchGoals = useGoalsStore((state) => state.fetchGoals);
  const [goalUpdates, setGoalUpdates] = useState<GoalStatusUpdate[]>([]);
  const [overallSummary, setOverallSummary] = useState("");
  const [blockers, setBlockers] = useState("");
  const [nextPeriodPlan, setNextPeriodPlan] = useState("");
  const [isFinal, setIsFinal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [checkinsRemaining] = useState(3);
  const [activeCycleId, setActiveCycleId] = useState<string | null>(null);

  useEffect(() => {
    fetchGoals().catch(() => null);
  }, [fetchGoals]);

  useEffect(() => {
    performanceCyclesService
      .listCycles()
      .then((payload) => {
        const active = (payload.cycles || []).find(
          (cycle) => String(cycle.status || "").toLowerCase() === "active"
        );
        setActiveCycleId(active?.id || null);
      })
      .catch(() => {
        setActiveCycleId(null);
      });
  }, []);

  useEffect(() => {
    // Pre-fill goal updates from last check-in (smart pre-filling)
    const approvedGoals = goals.filter(
      (g: Goal) => String(g.status || "").toLowerCase() === "approved"
    );

    // Prefer approved goals from the active cycle, but don't hide approved goals
    // when cycle ids are absent or out of sync between endpoints.
    const eligibleGoals = activeCycleId
      ? (() => {
          const activeCycleGoals = approvedGoals.filter(
            (g: Goal) => String(g.cycle_id || "") === activeCycleId
          );
          return activeCycleGoals.length > 0 ? activeCycleGoals : approvedGoals;
        })()
      : approvedGoals;

    setGoalUpdates(
      eligibleGoals.map((g: Goal) => ({
        goalId: g.id,
        title: g.title,
        rag: "GREEN" as const,
        progress: g.progress || 0,
      }))
    );
  }, [activeCycleId, goals]);

  const handleRagToggle = (goalId: string) => {
    setGoalUpdates((prev) =>
      prev.map((update) => {
        if (update.goalId === goalId) {
          return { ...update, rag: RAG_SEQUENCE[update.rag] };
        }
        return update;
      })
    );
  };

  const handleProgressChange = (goalId: string, progress: number) => {
    setGoalUpdates((prev) =>
      prev.map((update) =>
        update.goalId === goalId ? { ...update, progress } : update
      )
    );
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachments(Array.from(e.target.files));
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const summary = overallSummary.trim() || nextPeriodPlan.trim();
      if (!summary) {
        alert("Please add your update before submitting.");
        return;
      }

      const averageProgress = goalUpdates.length
        ? Math.round(goalUpdates.reduce((sum, item) => sum + item.progress, 0) / goalUpdates.length)
        : 0;

      await checkinsService.submit({
        overall_progress: averageProgress,
        summary,
        achievements: overallSummary.trim() || undefined,
        blockers: blockers.trim() || undefined,
        is_final: isFinal,
        goal_updates: goalUpdates.map((item) => ({
          goal_id: item.goalId,
          progress: item.progress,
          note: item.rag,
        })),
      });

      alert("✅ Check-in submitted successfully!");
      // Reset form after successful submission.
      setGoalUpdates([]);
      setOverallSummary("");
      setBlockers("");
      setNextPeriodPlan("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Check-in</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Q1 2025 · {checkinsRemaining} of 5 remaining
        </p>
      </div>

      <Card>
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            How are your goals going?
          </CardTitle>
          <CardDescription>Quick status update for each goal</CardDescription>
        </div>
        <div className="space-y-4">
          {goalUpdates.length === 0 ? (
            <p className="py-4 text-sm text-muted-foreground">
              No approved goals yet. Goals will appear here once approved.
            </p>
          ) : (
            goalUpdates.map((update) => (
              <div
                key={update.goalId}
                className="flex items-center gap-3 rounded-lg border border-border bg-card p-4"
              >
                {/* Goal Title */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground truncate">
                    {update.title}
                  </p>
                </div>

                {/* RAG Status Toggle */}
                <button
                  onClick={() => handleRagToggle(update.goalId)}
                  className={`flex h-7 w-7 items-center justify-center rounded-full border-2 ${
                    update.rag === "GREEN"
                      ? "border-emerald-600 bg-emerald-100 dark:border-emerald-400 dark:bg-emerald-900/30"
                      : update.rag === "AMBER"
                        ? "border-amber-600 bg-amber-100 dark:border-amber-400 dark:bg-amber-900/30"
                        : "border-red-600 bg-red-100 dark:border-red-400 dark:bg-red-900/30"
                  } flex-shrink-0 transition-colors`}
                  title="Click to cycle: 🟢 → 🟡 → 🔴"
                >
                  <span
                    className={`text-xs font-bold ${
                      update.rag === "GREEN"
                        ? "text-emerald-700 dark:text-emerald-300"
                        : update.rag === "AMBER"
                          ? "text-amber-700 dark:text-amber-300"
                          : "text-red-700 dark:text-red-300"
                    }`}
                  >
                    {update.rag === "GREEN" ? "🟢" : update.rag === "AMBER" ? "🟡" : "🔴"}
                  </span>
                </button>

                {/* Progress Slider */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={update.progress}
                    onChange={(e) =>
                      handleProgressChange(
                        update.goalId,
                        parseInt(e.target.value)
                      )
                    }
                    className="h-1.5 w-24 rounded-full"
                  />
                  <span className="w-10 text-right text-sm font-medium text-foreground">
                    {update.progress}%
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Overall Update Section */}
      <Card>
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Your Update
          </CardTitle>
          <CardDescription>3 fields only — focus on what&apos;s new</CardDescription>
        </div>
        <div className="space-y-4">
          {/* Accomplishment */}
          <div>
            <label className="block text-sm font-medium text-foreground">
              What did you accomplish this period?
            </label>
            <textarea
              value={overallSummary}
              onChange={(e) => setOverallSummary(e.target.value)}
              placeholder="Completed X, shipped Y, improved Z..."
              className="mt-2 min-h-20 w-full rounded-lg border border-input bg-card p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>

          {/* Blockers */}
          <div>
            <label className="block text-sm font-medium text-foreground">
              Any blockers? <span className="text-xs text-muted-foreground">(Optional)</span>
            </label>
            <textarea
              value={blockers}
              onChange={(e) => setBlockers(e.target.value)}
              placeholder="Waiting on X, QA blocker with Y..."
              className="mt-2 min-h-16 w-full rounded-lg border border-input bg-card p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>

          {/* Next Period Plan */}
          <div>
            <label className="block text-sm font-medium text-foreground">
              Your plan for next period?
            </label>
            <textarea
              value={nextPeriodPlan}
              onChange={(e) => setNextPeriodPlan(e.target.value)}
              placeholder="Planning to achieve A, focus on B, tackle C..."
              className="mt-2 min-h-16 w-full rounded-lg border border-input bg-card p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
        </div>
      </Card>

      {/* Attachments & Final Check-in */}
      <Card>
        <div>
          <CardTitle className="text-base">Supporting Materials</CardTitle>
        </div>
        <div className="space-y-4">
          <div>
            <label className="flex items-center gap-3 rounded-lg border-2 border-dashed border-border p-4 cursor-pointer hover:border-brand transition-colors">
              <Upload className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  📎 Attach proof or supporting doc
                </p>
                <p className="text-xs text-muted-foreground">
                  {attachments.length > 0
                    ? `${attachments.length} file(s) selected`
                    : "Optional — PDF, images, links"}
                </p>
              </div>
              <input
                type="file"
                multiple
                onChange={handleFileAttach}
                className="hidden"
              />
            </label>
          </div>

          {/* Final Check-in Checkbox */}
          <div className="flex items-center gap-3 rounded-lg border border-border p-4">
            <input
              type="checkbox"
              id="final-checkin"
              checked={isFinal}
              onChange={(e) => setIsFinal(e.target.checked)}
              className="h-4 w-4 rounded"
            />
            <label htmlFor="final-checkin" className="flex-1 text-sm cursor-pointer">
              <p className="font-medium text-foreground">
                ☐ This is my final check-in for this cycle
              </p>
              <p className="text-xs text-muted-foreground">
                After marking final, this cycle moves to rating phase
              </p>
            </label>
          </div>
        </div>
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" disabled={isLoading}>
          Save Draft
        </Button>
        <Button 
          onClick={handleSubmit} 
          disabled={isLoading || goalUpdates.length === 0}
          size="lg"
        >
          {isLoading ? "Submitting..." : "Submit Check-in →"}
        </Button>
      </div>

      {/* Help Text */}
      <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
        <div className="flex gap-3">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
          <div>
            <p className="text-sm font-medium text-foreground">💡 One submission covers all goals</p>
            <p className="mt-1 text-xs text-muted-foreground">
              No separate check-ins per goal. Update RAG status and progress for each
              goal above, write one overall narrative, and submit once. Your manager
              reviews everything in one integrated view.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
