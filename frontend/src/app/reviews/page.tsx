"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ClipboardList } from "lucide-react";
import { reviewsService } from "@/services/reviews";
import type { Review } from "@/types";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { PageHeader } from "@/components/ui/page-header";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);

  const loadReviews = () => reviewsService.getReviews().then(setReviews).catch(() => null);

  useEffect(() => {
    loadReviews();
  }, []);

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
