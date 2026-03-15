"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ClipboardList } from "lucide-react";
import { reviewsService } from "@/services/reviews";
import type { Review } from "@/types";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);

  const loadReviews = () => reviewsService.getReviews().then(setReviews).catch(() => null);

  useEffect(() => {
    loadReviews();
  }, []);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <PageHeader
        title="Reviews"
        description="Review ratings, summaries, strengths, and growth focus areas."
        action={<Button variant="outline" onClick={loadReviews}>Refresh</Button>}
      />

      <Card className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <ClipboardList className="h-3.5 w-3.5" /> Review Insights
        </div>
        <CardTitle>Performance Reviews</CardTitle>
        <CardDescription>Summaries, strengths, weaknesses, and growth focus areas.</CardDescription>
      </Card>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
        {reviews.map((review) => (
          <Card key={review.id} className="space-y-3 transition hover:-translate-y-0.5">
            <CardTitle>
              Cycle {review.cycle_year} Q{review.cycle_quarter}
            </CardTitle>
            <div className="text-sm text-muted-foreground">Rating: {review.overall_rating ?? "N/A"}</div>
            <div className="text-sm text-foreground"><span className="font-medium">Summary:</span> {review.summary || "-"}</div>
            <div className="text-sm text-foreground"><span className="font-medium">Strengths:</span> {review.strengths || "-"}</div>
            <div className="text-sm text-foreground"><span className="font-medium">Weaknesses:</span> {review.weaknesses || "-"}</div>
            <div className="text-sm text-foreground"><span className="font-medium">Growth:</span> {review.growth_areas || "-"}</div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}
