import { Skeleton } from "@/components/ui/skeleton";

export function StatCardSkeleton() {
  return (
    <div className="rounded-2xl border bg-card p-6">
      <Skeleton className="mb-4 h-4 w-24" />
      <Skeleton className="mb-2 h-8 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}

export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="w-full rounded-2xl border bg-card p-6" style={{ height }}>
      <Skeleton className="mb-4 h-4 w-32" />
      <Skeleton className="h-[calc(100%-2rem)] w-full" />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="overflow-hidden rounded-2xl border bg-card">
      <div className="h-12 border-b bg-muted/50" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 border-b p-4 last:border-0">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="ml-auto h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
      <ChartSkeleton height={350} />
      <TableSkeleton rows={6} />
    </div>
  );
}
