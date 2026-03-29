"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { adminService } from "@/services/admin";
import type { AdminDashboardPayload } from "@/types";

const CHART_COLORS = {
  blue: "#4F46E5",
  purple: "#7C3AED",
  pink: "#EC4899",
  cyan: "#06B6D4",
  green: "#10B981",
  yellow: "#F59E0B",
  red: "#EF4444",
  orange: "#FB923C",
};

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(17,24,39,0.95)",
  color: "#E5E7EB",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
};

export function AdminDashboard() {
  const [payload, setPayload] = useState<AdminDashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeRatingBarIndex, setActiveRatingBarIndex] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    adminService
      .getDashboard()
      .then(setPayload)
      .catch(() => setPayload(null))
      .finally(() => setLoading(false));
  }, []);

  const metricCards = useMemo(() => {
    const metrics = payload?.metrics;
    return [
      { key: "total_employees", label: "Total Employees", value: metrics?.total_employees ?? 0 },
      { key: "total_managers", label: "Total Managers", value: metrics?.total_managers ?? 0 },
      { key: "active_users", label: "Active Users", value: metrics?.active_users ?? 0 },
      { key: "total_goals", label: "Total Goals", value: metrics?.total_goals ?? 0 },
      { key: "active_checkins", label: "Active Check-ins", value: metrics?.active_checkins ?? 0 },
      { key: "meetings_scheduled", label: "Meetings Scheduled", value: metrics?.meetings_scheduled ?? 0 },
      { key: "avg_rating", label: "Avg Rating", value: (metrics?.avg_rating ?? 0).toFixed(2) },
    ];
  }, [payload]);

  const roleColorMap: Record<string, string> = {
    admin: CHART_COLORS.purple,
    hr: CHART_COLORS.pink,
    manager: CHART_COLORS.blue,
    employee: CHART_COLORS.cyan,
    leadership: CHART_COLORS.yellow,
  };

  const ratingColorMap: Record<string, string> = {
    EE: CHART_COLORS.green,
    DE: CHART_COLORS.blue,
    ME: CHART_COLORS.yellow,
    SME: CHART_COLORS.orange,
    NI: CHART_COLORS.red,
  };

  const employeeGrowth = payload?.employee_growth ?? [];
  const roleDistribution = payload?.role_distribution ?? [];
  const ratingDistribution = payload?.rating_distribution ?? [];

  const hasEmployeeGrowth = employeeGrowth.length > 0;
  const hasRoleDistribution = roleDistribution.length > 0;
  const hasRatingDistribution = ratingDistribution.length > 0;

  const roleLegend = roleDistribution.map((item) => ({
    role: String(item.role),
    color: roleColorMap[String(item.role)] || CHART_COLORS.cyan,
  }));

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => (
          <Card key={card.key} className="border border-border/70 transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-elevated">
            <CardDescription>{card.label}</CardDescription>
            <CardTitle className="mt-2 text-3xl">{card.value}</CardTitle>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardTitle>Employee Growth</CardTitle>
          <CardDescription>Monthly user onboarding trend</CardDescription>
          <div className="mt-4 h-80 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
            {loading ? (
              <Skeleton className="h-full w-full bg-white/5" />
            ) : hasEmployeeGrowth ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={employeeGrowth}>
                  <defs>
                    <linearGradient id="employeeGrowthGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor={CHART_COLORS.blue} />
                      <stop offset="100%" stopColor={CHART_COLORS.purple} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 4" vertical={false} />
                  <XAxis dataKey="month" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="url(#employeeGrowthGradient)"
                    strokeWidth={3}
                    dot={{ r: 4, fill: CHART_COLORS.blue, stroke: "#A5B4FC", strokeWidth: 2, style: { filter: "drop-shadow(0 0 8px rgba(79,70,229,0.8))" } }}
                    activeDot={{ r: 6, fill: CHART_COLORS.purple, stroke: "#C4B5FD", strokeWidth: 2 }}
                    isAnimationActive
                    animationDuration={800}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-[#9CA3AF]">No Data Available</div>
            )}
          </div>
        </Card>

        <Card>
          <CardTitle>Role Distribution</CardTitle>
          <CardDescription>Current workforce by role</CardDescription>
          <div className="mt-4 h-80 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
            {loading ? (
              <Skeleton className="h-full w-full bg-white/5" />
            ) : hasRoleDistribution ? (
              <>
                <ResponsiveContainer width="100%" height="85%">
                  <PieChart>
                    <Pie
                      data={roleDistribution}
                      dataKey="count"
                      nameKey="role"
                      innerRadius={55}
                      outerRadius={95}
                      paddingAngle={3}
                      isAnimationActive
                      animationDuration={800}
                    >
                      {roleDistribution.map((entry, index) => {
                        const roleKey = String(entry.role).toLowerCase();
                        return <Cell key={`${entry.role}-${index}`} fill={roleColorMap[roleKey] || CHART_COLORS.cyan} />;
                      })}
                    </Pie>
                    <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-1 flex flex-wrap justify-center gap-3">
                  {roleLegend.map((item) => (
                    <div key={item.role} className="flex items-center gap-2 text-xs text-[#E5E7EB]">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="capitalize">{item.role}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-[#9CA3AF]">No Data Available</div>
            )}
          </div>
        </Card>

        <Card className="xl:col-span-3">
          <CardTitle>Rating Distribution</CardTitle>
          <CardDescription>Performance ratings across the organization</CardDescription>
          <div className="mt-4 h-72 rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.02)] p-4 shadow-[0_12px_34px_rgba(0,0,0,0.24)]">
            {loading ? (
              <Skeleton className="h-full w-full bg-white/5" />
            ) : hasRatingDistribution ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={ratingDistribution}
                  onMouseMove={(state) => {
                    if (typeof state?.activeTooltipIndex === "number") {
                      setActiveRatingBarIndex(state.activeTooltipIndex);
                    }
                  }}
                  onMouseLeave={() => setActiveRatingBarIndex(null)}
                >
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 4" vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "#9CA3AF", fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#E5E7EB", fontWeight: 600, marginBottom: 4 }} />
                  <Bar dataKey="count" radius={[8, 8, 8, 8]} isAnimationActive animationDuration={700}>
                    {ratingDistribution.map((entry, index) => {
                      const label = String(entry.label);
                      const baseColor = ratingColorMap[label] || CHART_COLORS.blue;
                      const isActive = activeRatingBarIndex === index;
                      return (
                        <Cell
                          key={`rating-cell-${index}`}
                          fill={baseColor}
                          style={{
                            transition: "transform 180ms ease, filter 180ms ease",
                            transform: isActive ? "scale(1.04)" : "scale(1)",
                            transformOrigin: "center bottom",
                            filter: isActive ? "drop-shadow(0 0 10px rgba(255,255,255,0.25))" : "none",
                          }}
                        />
                      );
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-[#9CA3AF]">No Data Available</div>
            )}
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
