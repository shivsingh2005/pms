"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stat Cards Skeleton */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="space-y-3 rounded-2xl border border-border/75 bg-card/95 p-6">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-3 w-32" />
          </Card>
        ))}
      </section>

      {/* Next Action Skeleton */}
      <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 p-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-10 w-32" />
      </Card>

      {/* Top Attention Skeleton */}
      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 p-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-full" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        ))}
      </Card>

      {/* Insight Skeleton */}
      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 p-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-full" />
      </Card>
    </div>
  );
}
