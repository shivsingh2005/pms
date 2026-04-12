"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function LeadershipDashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Leadership Dashboard Error:", error);
  }, [error]);

  return (
    <div className="space-y-6">
      <Card className="space-y-4 rounded-2xl border border-red-200 bg-red-50">
        <CardTitle className="text-red-900">Leadership Dashboard Error</CardTitle>
        <CardDescription className="text-red-800">
          We encountered an error while loading your leadership dashboard. This might be a temporary issue.
        </CardDescription>

        <div className="space-y-3">
          <div className="rounded-lg bg-red-100 p-3">
            <p className="text-sm font-mono text-red-900">{error.message || "Unknown error"}</p>
          </div>

          <div className="flex gap-3">
            <Button onClick={() => reset()} variant="outline">
              Try Again
            </Button>
            <Link href="/leadership/org-dashboard">
              <Button variant="ghost">Reload Page</Button>
            </Link>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          If the problem persists, try logging out and back in. Contact support if the issue continues.
        </p>
      </Card>
    </div>
  );
}
