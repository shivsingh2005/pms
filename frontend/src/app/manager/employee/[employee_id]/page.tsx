"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Progress } from "@/components/ui/progress";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { managerService } from "@/services/manager";
import { useSessionStore } from "@/store/useSessionStore";
import type { ManagerEmployeeInspection } from "@/types";

export default function ManagerEmployeeInspectionPage() {
  const params = useParams<{ employee_id: string }>();
  const router = useRouter();
  const user = useSessionStore((s) => s.user);
  const [payload, setPayload] = useState<ManagerEmployeeInspection | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  useEffect(() => {
    if (!params.employee_id || !user) return;

    setLoading(true);
    managerService
      .inspectEmployee(params.employee_id)
      .then(setPayload)
      .catch(() => toast.error("Failed to load employee inspection"))
      .finally(() => setLoading(false));
  }, [params.employee_id, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Employee Performance Profile"
        description="Complete employee history including goals, check-ins, ratings, and AI insight signals."
        action={<Button variant="outline" onClick={() => router.back()}>Back</Button>}
      />

      {loading && <Card className="rounded-xl p-5 border bg-card"><CardDescription>Loading inspection data...</CardDescription></Card>}

      {!loading && payload && (
        <>
          <Card className="rounded-xl p-5 border bg-card space-y-2">
            <CardTitle>{payload.name}</CardTitle>
            <CardDescription>{payload.role} · {payload.department}</CardDescription>
            <p className="text-sm text-muted-foreground">{payload.email}</p>
          </Card>

          <section className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <Card className="rounded-xl p-4 border bg-card">
              <CardDescription>Overall Progress</CardDescription>
              <p className="mt-1 text-2xl font-semibold">{payload.progress}%</p>
              <Progress className="mt-3" value={payload.progress} />
            </Card>
            <Card className="rounded-xl p-4 border bg-card">
              <CardDescription>Goals Completed</CardDescription>
              <p className="mt-1 text-2xl font-semibold">{payload.goals_completed}</p>
            </Card>
            <Card className="rounded-xl p-4 border bg-card">
              <CardDescription>Consistency</CardDescription>
              <p className="mt-1 text-2xl font-semibold">{payload.consistency}%</p>
            </Card>
            <Card className="rounded-xl p-4 border bg-card">
              <CardDescription>Last Check-in</CardDescription>
              <p className="mt-1 text-sm font-semibold">
                {payload.last_checkin ? new Date(payload.last_checkin).toLocaleString() : "No check-ins yet"}
              </p>
            </Card>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="rounded-xl p-5 border bg-card space-y-3">
              <CardTitle>Goals History</CardTitle>
              {payload.goals.length === 0 ? (
                <CardDescription>No goals assigned.</CardDescription>
              ) : payload.goals.map((goal) => (
                <div key={goal.id} className="rounded-lg border border-border/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{goal.title}</p>
                    <Badge>{goal.status}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Progress: {goal.progress}%</p>
                </div>
              ))}
            </Card>

            <Card className="rounded-xl p-5 border bg-card space-y-3">
              <CardTitle>Check-in History</CardTitle>
              {payload.checkins.length === 0 ? (
                <CardDescription>No check-ins recorded.</CardDescription>
              ) : payload.checkins.map((row) => (
                <div key={row.id} className="rounded-lg border border-border/70 p-3">
                  <p className="font-medium">{new Date(row.meeting_date).toLocaleDateString()}</p>
                  {row.summary ? <p className="text-sm mt-2">{row.summary}</p> : null}
                  {row.notes ? <p className="text-xs text-muted-foreground mt-1">{row.notes}</p> : null}
                </div>
              ))}
            </Card>

            <Card className="rounded-xl p-5 border bg-card space-y-3">
              <CardTitle>Ratings</CardTitle>
              {payload.ratings.length === 0 ? (
                <CardDescription>No ratings found.</CardDescription>
              ) : payload.ratings.map((row) => (
                <div key={row.id} className="rounded-lg border border-border/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{row.rating}</p>
                    <p className="text-xs text-muted-foreground">{new Date(row.created_at).toLocaleDateString()}</p>
                  </div>
                  {row.comments ? <p className="text-sm mt-1">{row.comments}</p> : <p className="text-xs text-muted-foreground mt-1">No comments</p>}
                </div>
              ))}
            </Card>

            <Card className="rounded-xl p-5 border bg-card space-y-3">
              <CardTitle>AI Insights</CardTitle>
              <div className="rounded-lg border border-border/70 p-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Strengths</p>
                <p className="text-sm mt-1">{payload.ai_insights.strengths.join(", ")}</p>
              </div>
              <div className="rounded-lg border border-border/70 p-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Weaknesses</p>
                <p className="text-sm mt-1">{payload.ai_insights.weaknesses.join(", ")}</p>
              </div>
              <div className="rounded-lg border border-border/70 p-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Growth Areas</p>
                <p className="text-sm mt-1">{payload.ai_insights.growth_areas.join(", ")}</p>
              </div>
            </Card>
          </section>
        </>
      )}
    </motion.div>
  );
}
