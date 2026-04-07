"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ClipboardList } from "lucide-react";
import { reviewsService } from "@/services/reviews";
import type { Review, ReviewNarrative } from "@/types";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { PageHeader } from "@/components/ui/page-header";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [narrative, setNarrative] = useState<ReviewNarrative | null>(null);
  const [period, setPeriod] = useState<"quarter" | "year">("quarter");
  const [cycleYear, setCycleYear] = useState<number>(new Date().getFullYear());
  const [cycleQuarter, setCycleQuarter] = useState<number>(1);
  const [managerComments, setManagerComments] = useState("");
  const [isGeneratingNarrative, setIsGeneratingNarrative] = useState(false);

  const scopeLabel = useMemo(() => {
    if (!narrative) {
      return "-";
    }
    if (narrative.explainability.scope === "employee") {
      return "Employee";
    }
    if (narrative.explainability.scope === "team") {
      return "Team";
    }
    return "Organization";
  }, [narrative]);

  const loadReviews = useCallback(() => reviewsService.getReviews().then(setReviews).catch(() => null), []);

  const loadNarrative = useCallback(async () => {
    setIsGeneratingNarrative(true);
    try {
      const result = await reviewsService.getNarrative({
        period,
        cycle_year: cycleYear,
        cycle_quarter: period === "quarter" ? cycleQuarter : undefined,
        manager_comments: managerComments.trim() || undefined,
      });
      setNarrative(result);
    } finally {
      setIsGeneratingNarrative(false);
    }
  }, [period, cycleYear, cycleQuarter, managerComments]);

  useEffect(() => {
    loadReviews();
    loadNarrative().catch(() => null);
  }, [loadNarrative, loadReviews]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Reviews"
        description="Review ratings, summaries, strengths, and growth focus areas."
        action={<Button variant="outline" onClick={loadReviews}>Refresh</Button>}
      />

      <SectionContainer>
        <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <ClipboardList className="h-3.5 w-3.5" /> Review Insights
          </div>
          <CardTitle>Performance Reviews</CardTitle>
          <CardDescription>Summaries, strengths, weaknesses, and growth focus areas.</CardDescription>
        </Card>

        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 p-4">
          <CardTitle>AI Narrative Review</CardTitle>
          <CardDescription>
            Generate a period narrative with explainability metadata for employee, team, or organization review scope.
          </CardDescription>
          <div className="grid gap-3 md:grid-cols-4">
            <label className="space-y-1 text-sm">
              <span className="text-xs text-muted-foreground">Period</span>
              <select
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={period}
                onChange={(event) => setPeriod(event.target.value as "quarter" | "year")}
              >
                <option value="quarter">Quarter</option>
                <option value="year">Year</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-xs text-muted-foreground">Cycle Year</span>
              <Input
                type="number"
                min={2000}
                max={2100}
                value={cycleYear}
                onChange={(event) => setCycleYear(Number(event.target.value || new Date().getFullYear()))}
              />
            </label>
            {period === "quarter" ? (
              <label className="space-y-1 text-sm">
                <span className="text-xs text-muted-foreground">Cycle Quarter</span>
                <Input
                  type="number"
                  min={1}
                  max={4}
                  value={cycleQuarter}
                  onChange={(event) => setCycleQuarter(Number(event.target.value || 1))}
                />
              </label>
            ) : null}
            <div className="flex items-end">
              <Button className="w-full" onClick={() => loadNarrative().catch(() => null)} disabled={isGeneratingNarrative}>
                {isGeneratingNarrative ? "Generating..." : "Generate Narrative"}
              </Button>
            </div>
          </div>
          <label className="space-y-1 text-sm">
            <span className="text-xs text-muted-foreground">Manager Context (optional)</span>
            <Textarea
              value={managerComments}
              onChange={(event) => setManagerComments(event.target.value)}
              placeholder="Add context to steer narrative output"
            />
          </label>
          {narrative ? (
            <div className="space-y-3 rounded-xl border border-border/75 bg-background/40 p-4">
              <p className="text-sm font-medium text-foreground">{narrative.performance_summary}</p>
              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-1 text-sm">
                  <p className="font-medium">Strengths</p>
                  {(narrative.strengths.length ? narrative.strengths : ["No strengths generated"]).map((item, index) => (
                    <p key={`narrative-strength-${index}`} className="text-muted-foreground">• {item}</p>
                  ))}
                </div>
                <div className="space-y-1 text-sm">
                  <p className="font-medium">Weaknesses</p>
                  {(narrative.weaknesses.length ? narrative.weaknesses : ["No weaknesses generated"]).map((item, index) => (
                    <p key={`narrative-weakness-${index}`} className="text-muted-foreground">• {item}</p>
                  ))}
                </div>
                <div className="space-y-1 text-sm">
                  <p className="font-medium">Growth Plan</p>
                  {(narrative.growth_plan.length ? narrative.growth_plan : ["No growth plan generated"]).map((item, index) => (
                    <p key={`narrative-growth-${index}`} className="text-muted-foreground">• {item}</p>
                  ))}
                </div>
              </div>
              <div className="grid gap-2 rounded-lg border border-border/70 bg-card/70 p-3 text-xs text-muted-foreground md:grid-cols-3">
                <p>Scope: <span className="font-medium text-foreground">{scopeLabel}</span></p>
                <p>Source reviews: <span className="font-medium text-foreground">{narrative.explainability.review_count}</span></p>
                <p>
                  Filter: <span className="font-medium text-foreground">
                    {narrative.period === "quarter" ? `Q${narrative.cycle_quarter || "-"} ` : ""}
                    {narrative.cycle_year || "-"}
                  </span>
                </p>
              </div>
            </div>
          ) : null}
        </Card>

        <DataTable
          rows={reviews}
          rowKey={(row) => row.id}
          emptyState="No reviews available yet"
          columns={[
            {
              key: "cycle",
              header: "Cycle",
              render: (row) => `Q${row.cycle_quarter} ${row.cycle_year}`,
            },
            {
              key: "overall_rating",
              header: "Rating",
              render: (row) => row.overall_rating ?? "N/A",
            },
            {
              key: "summary",
              header: "Summary",
              render: (row) => row.summary || "-",
            },
            {
              key: "strengths",
              header: "Strengths",
              render: (row) => row.strengths || "-",
            },
            {
              key: "growth_areas",
              header: "Growth",
              render: (row) => row.growth_areas || "-",
            },
          ]}
        />
      </SectionContainer>
    </motion.div>
  );
}

