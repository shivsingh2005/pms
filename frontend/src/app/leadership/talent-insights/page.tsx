"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { MetricChart } from "@/components/dashboard/MetricChart";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeadershipPortalData } from "@/hooks/useLeadershipPortalData";
import { useSessionStore } from "@/store/useSessionStore";

const TALENT_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#EF4444"];

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(17,24,39,0.95)",
  color: "#E5E7EB",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
};

function riskBadgeClass(value: "Low" | "Medium" | "High") {
  if (value === "High") return "bg-red-500/10 text-red-700 ring-red-400/30";
  if (value === "Medium") return "bg-amber-500/10 text-amber-700 ring-amber-400/30";
  return "bg-emerald-500/10 text-emerald-700 ring-emerald-400/30";
}

export default function LeadershipTalentInsightsPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  const {
    loading,
    hasAnyData,
    emptyMessage,
    topPerformers,
    atRiskEmployees,
    talentDistribution,
    peopleInsights,
    trainingNeedSummary,
  } = useLeadershipPortalData({ range: "quarter" });

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Talent Insights</h1>
        <p className="text-sm text-muted-foreground">Leadership view of top talent, risk patterns, promotion readiness, and growth interventions.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-80 w-full rounded-2xl bg-white/5" />
        </div>
      ) : !hasAnyData ? (
        <Card className="rounded-2xl border border-dashed border-border/80 bg-card/70 text-center">
          <CardTitle>Talent Data Unavailable</CardTitle>
          <CardDescription className="mt-2">{emptyMessage}</CardDescription>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card className="rounded-2xl border border-border/75 bg-gradient-to-br from-blue-500/10 via-transparent to-blue-500/5">
              <CardTitle>Top Performers</CardTitle>
              <CardDescription>High-impact contributors with strong rating and progress signals.</CardDescription>
              <div className="mt-4 space-y-3">
                {topPerformers.length ? (
                  topPerformers.map((employee) => (
                    <div key={employee.id} className="rounded-xl border border-border/70 bg-card/70 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-foreground">{employee.name}</p>
                          <p className="text-xs text-muted-foreground">{employee.role}</p>
                        </div>
                        <Badge className={riskBadgeClass(employee.riskFlag)}>Risk {employee.riskFlag}</Badge>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                        <span>Rating {employee.rating.toFixed(2)}</span>
                        <span>Progress {employee.progress.toFixed(1)}%</span>
                      </div>
                      <Progress value={employee.progress} className="mt-2 h-2.5" />
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">{emptyMessage}</p>
                )}
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-gradient-to-br from-red-500/10 via-transparent to-amber-500/10">
              <CardTitle>At-Risk Employees</CardTitle>
              <CardDescription>Low rating, weak consistency, or stalled progress requiring intervention.</CardDescription>
              <div className="mt-4 space-y-3">
                {atRiskEmployees.length ? (
                  atRiskEmployees.map((employee) => (
                    <div key={employee.id} className="rounded-xl border border-border/70 bg-card/70 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-foreground">{employee.name}</p>
                          <p className="text-xs text-muted-foreground">{employee.role}</p>
                        </div>
                        <Badge className={riskBadgeClass(employee.riskFlag)}>Risk {employee.riskFlag}</Badge>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                        <span>Rating {employee.rating.toFixed(2)}</span>
                        <span>Progress {employee.progress.toFixed(1)}%</span>
                      </div>
                      <Progress value={employee.progress} className="mt-2 h-2.5" />
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">{emptyMessage}</p>
                )}
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Talent Distribution</CardTitle>
              <CardDescription>Rating bands to monitor bench strength and quality spread.</CardDescription>
              <div className="mt-4 h-72 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
                {talentDistribution.some((entry) => entry.count > 0) ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={talentDistribution} dataKey="count" nameKey="band" innerRadius={45} outerRadius={92} paddingAngle={3}>
                        {talentDistribution.map((entry, index) => (
                          <Cell key={`${entry.band}-${index}`} fill={TALENT_COLORS[index % TALENT_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">{emptyMessage}</div>
                )}
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Promotion Readiness</CardTitle>
              <CardDescription>AI-based readiness signal from performance, consistency, and final rating.</CardDescription>
              <div className="mt-4">
                <MetricChart
                  kind="bar"
                  data={[
                    { stage: "Ready Now", value: peopleInsights.filter((entry) => entry.promotionReadiness === "Ready Now").length },
                    { stage: "Ready in 1-2 cycles", value: peopleInsights.filter((entry) => entry.promotionReadiness === "Ready in 1-2 cycles").length },
                    { stage: "Needs Development", value: peopleInsights.filter((entry) => entry.promotionReadiness === "Needs Development").length },
                  ]}
                  xKey="stage"
                  yKey="value"
                  color="#10B981"
                  barPalette={{
                    "Ready Now": "#10B981",
                    "Ready in 1-2 cycles": "#F59E0B",
                    "Needs Development": "#EF4444",
                  }}
                />
              </div>
            </Card>
          </div>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Training Need Insights</CardTitle>
            <CardDescription>Heatmap-linked training demand by severity band.</CardDescription>
            <div className="mt-4">
              <MetricChart
                kind="bar"
                data={trainingNeedSummary}
                xKey="label"
                yKey="value"
                color="#F59E0B"
                barPalette={{
                  "No Need": "#22C55E",
                  Low: "#84CC16",
                  Medium: "#F59E0B",
                  High: "#EF4444",
                  Critical: "#B91C1C",
                }}
              />
            </div>
          </Card>
        </>
      )}
    </motion.div>
  );
}
