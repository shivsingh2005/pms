"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { hrService } from "@/services/hr";
import type { HROverview, HROrgAnalytics } from "@/types";

const CHART_COLORS = {
  lineStart: "#2563EB",
  lineEnd: "#14B8A6",
  barA: "#1D4ED8",
  barB: "#0EA5E9",
  barC: "#10B981",
  pieA: "#16A34A",
  pieB: "#FACC15",
  pieC: "#F97316",
  pieD: "#DC2626",
};

function normalizeLevel(level: string): "No Need" | "Low" | "Medium" | "High" | "Critical" {
  if (level === "Critical" || level === "High" || level === "Medium" || level === "Low") {
    return level;
  }
  return "No Need";
}

function levelToRisk(level: "No Need" | "Low" | "Medium" | "High" | "Critical"): "Low" | "Medium" | "High" | "Critical" {
  if (level === "Critical") return "Critical";
  if (level === "High") return "High";
  if (level === "Medium") return "Medium";
  return "Low";
}

function scoreFromCell(level: "No Need" | "Low" | "Medium" | "High" | "Critical", intensity: number): number {
  const base = {
    "No Need": 12,
    Low: 30,
    Medium: 56,
    High: 78,
    Critical: 95,
  }[level];
  return Math.max(0, Math.min(100, base + (intensity - 0.5) * 14));
}

function gradientColorFromScore(score: number) {
  const clamped = Math.max(0, Math.min(100, score));
  const hue = 142 - (142 * clamped) / 100;
  const shadeA = `hsl(${Math.round(hue)} 80% 52%)`;
  const shadeB = `hsl(${Math.max(2, Math.round(hue - 10))} 85% 42%)`;
  return `linear-gradient(135deg, ${shadeA}, ${shadeB})`;
}

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(148, 163, 184, 0.35)",
  backgroundColor: "rgba(241, 245, 249, 0.93)",
  color: "#0F172A",
  padding: "10px 12px",
  boxShadow: "0 10px 24px rgba(15, 23, 42, 0.15)",
};

export function HRDashboard() {
  const [overview, setOverview] = useState<HROverview | null>(null);
  const [analytics, setAnalytics] = useState<HROrgAnalytics | null>(null);
  const [directory, setDirectory] = useState<Array<{ id: string; role: string; department: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState("all");
  const [selectedDepartment, setSelectedDepartment] = useState("all");
  const [selectedRisk, setSelectedRisk] = useState("all");
  const [viewMode, setViewMode] = useState<"compact" | "detailed">("detailed");
  const [activeEmployeeId, setActiveEmployeeId] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    if (typeof document === "undefined") return;

    const root = document.documentElement;
    const syncTheme = () => setIsDarkMode(root.classList.contains("dark"));
    syncTheme();

    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const themedTooltipStyle = useMemo(
    () =>
      isDarkMode
        ? {
            ...chartTooltipStyle,
            border: "1px solid rgba(148, 163, 184, 0.3)",
            backgroundColor: "rgba(15, 23, 42, 0.94)",
            color: "#E2E8F0",
            boxShadow: "0 10px 24px rgba(2, 6, 23, 0.45)",
          }
        : chartTooltipStyle,
    [isDarkMode],
  );

  useEffect(() => {
    setLoading(true);
    Promise.all([
      hrService.getOverview().catch(() => null),
      hrService.getOrgAnalytics().catch(() => null),
      hrService.getEmployees().catch(() => []),
    ])
      .then(([overviewData, analyticsData, employees]) => {
        setOverview(overviewData);
        setAnalytics(analyticsData);
        setDirectory((employees ?? []).map((item) => ({ id: item.id, role: item.role, department: item.department })));
      })
      .finally(() => setLoading(false));
  }, []);

  const employeeMetaById = useMemo(() => {
    const map = new Map<string, { role: string; department: string }>();
    for (const employee of directory) {
      map.set(employee.id, { role: employee.role, department: employee.department });
    }
    return map;
  }, [directory]);

  const allHeatmapCells = useMemo(
    () =>
      (overview?.training_heatmap ?? []).map((cell, index) => {
        const level = normalizeLevel(cell.training_need_level);
        const riskLevel = levelToRisk(level);
        const meta = employeeMetaById.get(cell.employee_id);
        return {
          ...cell,
          anonymousLabel: `Employee ${index + 1}`,
          level,
          riskLevel,
          role: meta?.role ?? "Unassigned",
          department: meta?.department ?? "Unassigned",
          score: scoreFromCell(level, cell.intensity),
        };
      }),
    [employeeMetaById, overview?.training_heatmap],
  );

  const roleOptions = useMemo(() => {
    const set = new Set<string>();
    for (const cell of allHeatmapCells) {
      set.add(cell.role);
    }
    return ["all", ...Array.from(set).sort((a, b) => a.localeCompare(b))];
  }, [allHeatmapCells]);

  const departmentOptions = useMemo(() => {
    const set = new Set<string>();
    for (const cell of allHeatmapCells) {
      set.add(cell.department);
    }
    return ["all", ...Array.from(set).sort((a, b) => a.localeCompare(b))];
  }, [allHeatmapCells]);

  const filteredHeatmapCells = useMemo(
    () =>
      allHeatmapCells.filter((cell) => {
        const roleMatch = selectedRole === "all" || cell.role === selectedRole;
        const departmentMatch = selectedDepartment === "all" || cell.department === selectedDepartment;
        const riskMatch = selectedRisk === "all" || cell.riskLevel === selectedRisk;
        return roleMatch && departmentMatch && riskMatch;
      }),
    [allHeatmapCells, selectedDepartment, selectedRisk, selectedRole],
  );

  useEffect(() => {
    if (!filteredHeatmapCells.length) {
      setActiveEmployeeId(null);
      return;
    }
    const stillVisible = filteredHeatmapCells.some((cell) => cell.employee_id === activeEmployeeId);
    if (!stillVisible) {
      setActiveEmployeeId(filteredHeatmapCells[0].employee_id);
    }
  }, [activeEmployeeId, filteredHeatmapCells]);

  const activeCell = useMemo(
    () => filteredHeatmapCells.find((cell) => cell.employee_id === activeEmployeeId) ?? null,
    [activeEmployeeId, filteredHeatmapCells],
  );

  const legend = useMemo(
    () => [
      { label: "Low", color: gradientColorFromScore(20) },
      { label: "Medium", color: gradientColorFromScore(52) },
      { label: "High", color: gradientColorFromScore(76) },
      { label: "Critical", color: gradientColorFromScore(96) },
    ],
    [],
  );

  const performanceTrend = analytics?.performance_trend ?? [];
  const teamPerformance = analytics?.department_comparison ?? [];
  const ratingDistribution = analytics?.rating_distribution ?? [];
  const roleDistribution = useMemo(() => {
    const counts = new Map<string, number>();
    for (const employee of directory) {
      counts.set(employee.role, (counts.get(employee.role) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([role, count]) => ({ role, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [directory]);

  const compactCellSize = 28;
  const detailedCellSize = 38;
  const cellSize = viewMode === "compact" ? compactCellSize : detailedCellSize;

  return (
    <motion.div className="space-y-6" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: "easeOut" }}>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-2xl border border-white/40 bg-white/55 shadow-[0_14px_34px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_18px_38px_rgba(2,6,23,0.45)]">
          <CardTitle>Total Employees</CardTitle>
          <CardDescription>{loading ? "..." : overview?.total_employees ?? 0}</CardDescription>
        </Card>
        <Card className="rounded-2xl border border-white/40 bg-white/55 shadow-[0_14px_34px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_18px_38px_rgba(2,6,23,0.45)]">
          <CardTitle>Total Managers</CardTitle>
          <CardDescription>{loading ? "..." : overview?.total_managers ?? 0}</CardDescription>
        </Card>
        <Card className="rounded-2xl border border-white/40 bg-white/55 shadow-[0_14px_34px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_18px_38px_rgba(2,6,23,0.45)]">
          <CardTitle>At-Risk Employees</CardTitle>
          <CardDescription>{loading ? "..." : overview?.at_risk_employees ?? 0}</CardDescription>
        </Card>
        <Card className="rounded-2xl border border-white/40 bg-white/55 shadow-[0_14px_34px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_18px_38px_rgba(2,6,23,0.45)]">
          <CardTitle>Avg Org Performance</CardTitle>
          <CardDescription>{loading ? "..." : `${overview?.avg_org_performance ?? 0}%`}</CardDescription>
        </Card>
      </div>

      <Card className="space-y-5 rounded-2xl border border-white/40 bg-white/55 shadow-[0_16px_38px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_22px_44px_rgba(2,6,23,0.48)]">
        <div>
          <CardTitle>Performance Analytics</CardTitle>
          <CardDescription>Live org-level trend, team performance, role mix, and rating distribution.</CardDescription>
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 shadow-[0_8px_22px_rgba(15,23,42,0.08)] transition-transform duration-200 hover:-translate-y-0.5 dark:border-slate-700/60 dark:bg-slate-900/65 dark:shadow-[0_12px_28px_rgba(2,6,23,0.4)]">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Org Performance Trend</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Monthly progression of average performance</p>
            <div className="mt-3 h-72">
              {loading ? (
                <Skeleton className="h-full w-full bg-slate-200/70 dark:bg-slate-700/40" />
              ) : performanceTrend.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceTrend}>
                    <defs>
                      <linearGradient id="hrTrendGradientInline" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor={CHART_COLORS.lineStart} />
                        <stop offset="100%" stopColor={CHART_COLORS.lineEnd} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(148, 163, 184, 0.35)" strokeDasharray="3 4" vertical={false} />
                    <XAxis dataKey="week" tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={themedTooltipStyle} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="url(#hrTrendGradientInline)"
                      strokeWidth={3}
                      dot={{ r: 3, fill: CHART_COLORS.lineStart, stroke: "#DBEAFE", strokeWidth: 2 }}
                      activeDot={{ r: 6, fill: CHART_COLORS.lineEnd, stroke: "#CCFBF1", strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-500 dark:text-slate-400">No data available</div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 shadow-[0_8px_22px_rgba(15,23,42,0.08)] transition-transform duration-200 hover:-translate-y-0.5 dark:border-slate-700/60 dark:bg-slate-900/65 dark:shadow-[0_12px_28px_rgba(2,6,23,0.4)]">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Team-wise Performance</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Average performance split by department teams</p>
            <div className="mt-3 h-72">
              {loading ? (
                <Skeleton className="h-full w-full bg-slate-200/70 dark:bg-slate-700/40" />
              ) : teamPerformance.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamPerformance}>
                    <CartesianGrid stroke="rgba(148, 163, 184, 0.35)" strokeDasharray="3 4" vertical={false} />
                    <XAxis dataKey="department" tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={themedTooltipStyle} />
                    <Bar dataKey="value" radius={[10, 10, 6, 6]}>
                      {teamPerformance.map((_, index) => {
                        const fills = [CHART_COLORS.barA, CHART_COLORS.barB, CHART_COLORS.barC];
                        return <Cell key={`team-performance-cell-${index}`} fill={fills[index % fills.length]} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-500 dark:text-slate-400">No data available</div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 shadow-[0_8px_22px_rgba(15,23,42,0.08)] transition-transform duration-200 hover:-translate-y-0.5 dark:border-slate-700/60 dark:bg-slate-900/65 dark:shadow-[0_12px_28px_rgba(2,6,23,0.4)]">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Role Distribution</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Current workforce split by roles</p>
            <div className="mt-3 h-72">
              {loading ? (
                <Skeleton className="h-full w-full bg-slate-200/70 dark:bg-slate-700/40" />
              ) : roleDistribution.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={roleDistribution} dataKey="count" nameKey="role" innerRadius={50} outerRadius={96} paddingAngle={3}>
                      {roleDistribution.map((_, index) => {
                        const fills = [CHART_COLORS.pieA, CHART_COLORS.pieB, CHART_COLORS.pieC, CHART_COLORS.pieD];
                        return <Cell key={`role-cell-${index}`} fill={fills[index % fills.length]} />;
                      })}
                    </Pie>
                    <Tooltip contentStyle={themedTooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-500 dark:text-slate-400">No data available</div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 shadow-[0_8px_22px_rgba(15,23,42,0.08)] transition-transform duration-200 hover:-translate-y-0.5 dark:border-slate-700/60 dark:bg-slate-900/65 dark:shadow-[0_12px_28px_rgba(2,6,23,0.4)]">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Rating Distribution</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Employee rating buckets across the organization</p>
            <div className="mt-3 h-72">
              {loading ? (
                <Skeleton className="h-full w-full bg-slate-200/70 dark:bg-slate-700/40" />
              ) : ratingDistribution.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ratingDistribution}>
                    <CartesianGrid stroke="rgba(148, 163, 184, 0.35)" strokeDasharray="3 4" vertical={false} />
                    <XAxis dataKey="label" tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={themedTooltipStyle} />
                    <Bar dataKey="count" radius={[10, 10, 6, 6]} fill="#7C3AED" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-500 dark:text-slate-400">No data available</div>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Card className="space-y-4 rounded-2xl border border-white/40 bg-white/55 shadow-[0_16px_38px_rgba(15,23,42,0.1)] backdrop-blur-xl dark:border-slate-700/70 dark:bg-slate-900/55 dark:shadow-[0_22px_44px_rgba(2,6,23,0.48)]">
        <CardTitle>Training Need Heatmap</CardTitle>
        <CardDescription>Anonymous, filterable training-intensity view with fixed details pane.</CardDescription>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-4">
          <label className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-300">Role</span>
            <select
              value={selectedRole}
              onChange={(event) => setSelectedRole(event.target.value)}
              className="h-10 w-full rounded-lg border border-slate-300/80 bg-white/80 px-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-300/60 dark:border-slate-700/70 dark:bg-slate-900/80 dark:text-slate-100 dark:focus:border-slate-500 dark:focus:ring-slate-700/60"
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role === "all" ? "All Roles" : role}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-300">Department</span>
            <select
              value={selectedDepartment}
              onChange={(event) => setSelectedDepartment(event.target.value)}
              className="h-10 w-full rounded-lg border border-slate-300/80 bg-white/80 px-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-300/60 dark:border-slate-700/70 dark:bg-slate-900/80 dark:text-slate-100 dark:focus:border-slate-500 dark:focus:ring-slate-700/60"
            >
              {departmentOptions.map((department) => (
                <option key={department} value={department}>
                  {department === "all" ? "All Departments" : department}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-300">Risk Level</span>
            <select
              value={selectedRisk}
              onChange={(event) => setSelectedRisk(event.target.value)}
              className="h-10 w-full rounded-lg border border-slate-300/80 bg-white/80 px-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-300/60 dark:border-slate-700/70 dark:bg-slate-900/80 dark:text-slate-100 dark:focus:border-slate-500 dark:focus:ring-slate-700/60"
            >
              {[
                { label: "All Risks", value: "all" },
                { label: "Low", value: "Low" },
                { label: "Medium", value: "Medium" },
                { label: "High", value: "High" },
                { label: "Critical", value: "Critical" },
              ].map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-600 dark:text-slate-300">View Mode</span>
            <div className="grid h-10 grid-cols-2 rounded-lg border border-slate-300/80 bg-white/80 p-1 shadow-sm dark:border-slate-700/70 dark:bg-slate-900/80">
              <Button
                variant={viewMode === "compact" ? "default" : "ghost"}
                size="sm"
                className={cn("h-full rounded-md text-xs", viewMode === "compact" ? "shadow-sm" : "text-slate-600 dark:text-slate-300")}
                onClick={() => setViewMode("compact")}
              >
                Compact
              </Button>
              <Button
                variant={viewMode === "detailed" ? "default" : "ghost"}
                size="sm"
                className={cn("h-full rounded-md text-xs", viewMode === "detailed" ? "shadow-sm" : "text-slate-600 dark:text-slate-300")}
                onClick={() => setViewMode("detailed")}
              >
                Detailed
              </Button>
            </div>
          </div>
        </div>

        {loading ? (
          <Skeleton className="h-72 bg-slate-200/70 dark:bg-slate-700/40" />
        ) : filteredHeatmapCells.length === 0 ? (
          <p className="text-sm text-muted-foreground">No training data available.</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
              <div className="rounded-2xl border border-slate-200/80 bg-white/65 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-slate-700/60 dark:bg-slate-900/65 dark:shadow-[0_14px_30px_rgba(2,6,23,0.45)]">
                <div
                  className={cn(
                    "grid gap-2",
                    viewMode === "compact"
                      ? "grid-cols-[repeat(auto-fit,minmax(28px,1fr))]"
                      : "grid-cols-[repeat(auto-fit,minmax(38px,1fr))]",
                  )}
                >
                  {filteredHeatmapCells.map((cell) => {
                    const selected = cell.employee_id === activeEmployeeId;
                  return (
                      <button
                        key={cell.employee_id}
                        type="button"
                        onMouseEnter={() => setActiveEmployeeId(cell.employee_id)}
                        onFocus={() => setActiveEmployeeId(cell.employee_id)}
                        onClick={() => setActiveEmployeeId(cell.employee_id)}
                        className={cn(
                          "group relative rounded-md border text-left transition-all duration-200",
                          selected
                            ? "border-slate-700/80 ring-2 ring-slate-500/45 dark:border-cyan-400/60 dark:ring-cyan-500/35"
                            : "border-white/30 hover:-translate-y-0.5 hover:shadow-[0_8px_16px_rgba(15,23,42,0.2)]",
                        )}
                        style={{
                          width: `${cellSize}px`,
                          height: `${cellSize}px`,
                          background: gradientColorFromScore(cell.score),
                        }}
                        aria-label={`${cell.anonymousLabel} training need ${cell.level}`}
                      >
                        {viewMode === "detailed" ? (
                          <span className="absolute inset-0 flex items-center justify-center text-[9px] font-semibold text-white/90">
                            {cell.anonymousLabel.split(" ")[1]}
                          </span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200/80 bg-white/75 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.12)] backdrop-blur-xl dark:border-slate-700/60 dark:bg-slate-900/72 dark:shadow-[0_16px_32px_rgba(2,6,23,0.48)]">
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Employee Details</p>
                {activeCell ? (
                  <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                    <p className="rounded-md bg-slate-100/80 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-700 dark:bg-slate-800/85 dark:text-slate-100">{activeCell.anonymousLabel}</p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Performance:</span> {activeCell.progress.toFixed(1)}%
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Consistency:</span> {activeCell.consistency.toFixed(1)}%
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Rating:</span>{" "}
                      {activeCell.rating !== null && activeCell.rating !== undefined ? activeCell.rating.toFixed(2) : "N/A"}
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Training Need:</span> {activeCell.level}
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Risk Level:</span> {activeCell.riskLevel}
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Department:</span> {activeCell.department}
                    </p>
                    <p>
                      <span className="font-medium text-slate-700 dark:text-slate-100">Role:</span> {activeCell.role}
                    </p>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">Hover or focus a heatmap cell to inspect details.</p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-200/80 bg-white/65 px-4 py-3 text-xs shadow-sm dark:border-slate-700/60 dark:bg-slate-900/65">
              {legend.map((item) => (
                <div key={item.label} className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                  <span className="inline-block h-4 w-4 rounded-md border border-slate-200" style={{ background: item.color }} />
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
