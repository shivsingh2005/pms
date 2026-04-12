"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Gauge,
  ShieldAlert,
  Sparkles,
  Users,
  Search,
  ChevronDown,
  Trophy,
  TrendingDown,
} from "lucide-react";
import { LazyPieChart } from "@/components/charts";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { hrService } from "@/services/hr";
import type { HRManagerOption, HRManagerTeamSummary } from "@/types";

const PIE_COLORS = {
  low: "#ef4444",
  medium: "#facc15",
  high: "#22c55e",
};

const chartTooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  backgroundColor: "rgba(15,23,42,0.95)",
  color: "#e2e8f0",
  padding: "10px 12px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
};

function initials(name: string): string {
  const parts = name.trim().split(" ").filter(Boolean);
  if (!parts.length) return "NA";
  return parts.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "").join("");
}

function clampProgress(value: number): number {
  return Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
}

export default function HRManagerTeamViewPage() {
  const [managers, setManagers] = useState<HRManagerOption[]>([]);
  const [selectedManager, setSelectedManager] = useState("");
  const [payload, setPayload] = useState<HRManagerTeamSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [managerOpen, setManagerOpen] = useState(false);
  const [managerQuery, setManagerQuery] = useState("");
  const managerPickerRef = useRef<HTMLDivElement | null>(null);
  const managerTriggerRef = useRef<HTMLButtonElement | null>(null);
  const managerMenuRef = useRef<HTMLDivElement | null>(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0, width: 0 });

  useEffect(() => {
    hrService.getManagers().then((items) => {
      setManagers(items);
      if (items[0]) setSelectedManager(items[0].id);
    }).catch(() => null);
  }, []);

  useEffect(() => {
    if (!selectedManager) return;
    setIsLoading(true);
    hrService.getManagerTeamAnalytics(selectedManager).then(setPayload).catch(() => setPayload(null)).finally(() => setIsLoading(false));
  }, [selectedManager]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      const insidePicker = managerPickerRef.current?.contains(target);
      const insideMenu = managerMenuRef.current?.contains(target);
      if (!insidePicker && !insideMenu) {
        setManagerOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    function updateMenuPosition() {
      if (!managerTriggerRef.current) return;
      const rect = managerTriggerRef.current.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + 8,
        left: rect.left,
        width: rect.width,
      });
    }

    if (!managerOpen) return;
    updateMenuPosition();

    window.addEventListener("resize", updateMenuPosition);
    window.addEventListener("scroll", updateMenuPosition, true);
    return () => {
      window.removeEventListener("resize", updateMenuPosition);
      window.removeEventListener("scroll", updateMenuPosition, true);
    };
  }, [managerOpen]);

  const selectedManagerData = useMemo(
    () => managers.find((manager) => manager.id === selectedManager) ?? null,
    [managers, selectedManager],
  );

  const filteredManagers = useMemo(() => {
    const query = managerQuery.trim().toLowerCase();
    if (!query) return managers;
    return managers.filter((manager) => {
      const hay = `${manager.name} ${manager.email ?? ""} ${manager.department ?? ""}`.toLowerCase();
      return hay.includes(query);
    });
  }, [managerQuery, managers]);

  const ratingDonut = useMemo(() => {
    const initial = { low: 0, medium: 0, high: 0 };
    if (!payload) return initial;

    for (const row of payload.rating_distribution) {
      const label = row.label.toUpperCase();
      if (label === "NI" || label === "SME" || label === "1" || label === "2") {
        initial.low += row.count;
      } else if (label === "ME" || label === "3") {
        initial.medium += row.count;
      } else {
        initial.high += row.count;
      }
    }
    return initial;
  }, [payload]);

  const donutData = useMemo(
    () => [
      { name: "1-2", value: ratingDonut.low, color: PIE_COLORS.low },
      { name: "3", value: ratingDonut.medium, color: PIE_COLORS.medium },
      { name: "4-5", value: ratingDonut.high, color: PIE_COLORS.high },
    ],
    [ratingDonut],
  );

  const maxWorkload = useMemo(() => {
    if (!payload?.workload_distribution.length) return 100;
    return Math.max(100, ...payload.workload_distribution.map((row) => row.weightage));
  }, [payload?.workload_distribution]);

  const topPerformerCards = payload?.top_performers ?? [];
  const lowPerformerCards = payload?.low_performers ?? [];

  const statusBadgeClass = (status: string) => {
    if (status === "On Track") return "bg-emerald-500/20 text-emerald-200 border-emerald-400/30";
    if (status === "Needs Attention") return "bg-amber-500/20 text-amber-200 border-amber-400/30";
    return "bg-rose-500/20 text-rose-200 border-rose-400/30";
  };

  const statusLabel = (status: string) => {
    if (status === "At Risk") return "Critical";
    return status;
  };

  return (
    <div className="min-h-screen rounded-3xl bg-[radial-gradient(circle_at_top,_#1e293b,_#020617)] p-6 text-slate-100 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Manager Team Analytics</h1>
          <p className="text-sm text-slate-300">Premium visibility into team health, performance, risk, and workload in one scan-friendly workspace.</p>
        </div>

        <Card className="dashboard-layer-top overflow-visible rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(56,189,248,0.2)]">
          <CardTitle className="text-white">Select Manager</CardTitle>
          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <div className="dashboard-dropdown-root flex-1" ref={managerPickerRef}>
              <button
                ref={managerTriggerRef}
                type="button"
                onClick={() => setManagerOpen((prev) => !prev)}
                className="flex h-12 w-full items-center justify-between rounded-xl border border-white/15 bg-slate-950/50 px-3 text-left transition duration-300 hover:border-cyan-400/40"
              >
                <span className="flex items-center gap-3">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/25 text-xs font-semibold text-cyan-100">
                    {initials(selectedManagerData?.name ?? "Manager")}
                  </span>
                  <span>
                    <span className="block text-sm font-semibold text-slate-100">{selectedManagerData?.name ?? "Select manager"}</span>
                    <span className="block text-xs text-slate-400">{selectedManagerData?.department || "No department"}</span>
                  </span>
                </span>
                <ChevronDown className="h-4 w-4 text-slate-300" />
              </button>

              {managerOpen && typeof document !== "undefined"
                ? createPortal(
                  <div
                    ref={managerMenuRef}
                    className="dashboard-dropdown-menu rounded-xl border border-white/15 bg-slate-950/95 p-2 backdrop-blur-xl"
                    style={{
                      top: `${menuPosition.top}px`,
                      left: `${menuPosition.left}px`,
                      width: `${menuPosition.width}px`,
                    }}
                  >
                  <div className="relative mb-2">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                    <input
                      value={managerQuery}
                      onChange={(event) => setManagerQuery(event.target.value)}
                      placeholder="Search manager"
                      className="h-10 w-full rounded-lg border border-white/10 bg-slate-900/70 pl-9 pr-3 text-sm text-slate-100 outline-none placeholder:text-slate-500"
                    />
                  </div>
                  <div className="max-h-56 overflow-y-auto">
                    {filteredManagers.length === 0 ? (
                      <p className="px-2 py-3 text-sm text-slate-400">No manager found.</p>
                    ) : (
                      filteredManagers.map((manager) => (
                        <button
                          key={manager.id}
                          type="button"
                          onClick={() => {
                            setSelectedManager(manager.id);
                            setManagerOpen(false);
                          }}
                          className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition duration-300 hover:bg-white/10"
                        >
                          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-indigo-500/30 text-xs font-semibold text-indigo-100">
                            {initials(manager.name)}
                          </span>
                          <span>
                            <span className="block text-sm font-medium text-slate-100">{manager.name}</span>
                            <span className="block text-xs text-slate-400">{manager.department || "No department"}</span>
                          </span>
                        </button>
                      ))
                    )}
                  </div>
                  </div>,
                  document.body,
                )
                : null}
            </div>
            <Button
              variant="outline"
              className="h-12 rounded-xl border-white/20 bg-white/5 text-slate-100 hover:bg-white/10"
              onClick={() => selectedManager && hrService.getManagerTeamAnalytics(selectedManager).then(setPayload).catch(() => null)}
            >
              Refresh
            </Button>
          </div>
        </Card>

        {!payload ? (
          <Card className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <CardDescription className="text-slate-300">{isLoading ? "Loading analytics..." : "Select a manager to view analytics."}</CardDescription>
          </Card>
        ) : (
          <>
            <div className="dashboard-layer-base grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="rounded-2xl border border-blue-300/20 bg-gradient-to-br from-blue-500/35 to-indigo-700/35 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(59,130,246,0.4)]">
                <div className="flex items-center justify-between">
                  <Users className="h-5 w-5 text-blue-100" />
                  <span className="text-xs text-blue-100/80">Live</span>
                </div>
                <p className="mt-4 text-4xl font-extrabold text-white">{payload.team_size}</p>
                <p className="text-sm text-blue-100/90">Team Size</p>
              </Card>

              <Card className="rounded-2xl border border-emerald-300/20 bg-gradient-to-br from-emerald-500/35 to-teal-700/35 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(16,185,129,0.4)]">
                <div className="flex items-center justify-between">
                  <Gauge className="h-5 w-5 text-emerald-100" />
                  <span className="text-xs text-emerald-100/80">Average</span>
                </div>
                <p className="mt-4 text-4xl font-extrabold text-white">{payload.avg_performance}%</p>
                <p className="text-sm text-emerald-100/90">Avg Performance</p>
              </Card>

              <Card className="rounded-2xl border border-violet-300/20 bg-gradient-to-br from-violet-500/35 to-fuchsia-700/35 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(168,85,247,0.4)]">
                <div className="flex items-center justify-between">
                  <Sparkles className="h-5 w-5 text-violet-100" />
                  <span className="text-xs text-violet-100/80">Health</span>
                </div>
                <p className="mt-4 text-4xl font-extrabold text-white">{payload.consistency}%</p>
                <p className="text-sm text-violet-100/90">Consistency</p>
              </Card>

              <Card className="rounded-2xl border border-rose-300/20 bg-gradient-to-br from-rose-500/35 to-red-700/35 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(244,63,94,0.4)]">
                <div className="flex items-center justify-between">
                  <ShieldAlert className="h-5 w-5 text-rose-100" />
                  <span className="text-xs text-rose-100/80">Action</span>
                </div>
                <p className="mt-4 text-4xl font-extrabold text-white">{payload.at_risk_employees}</p>
                <p className="text-sm text-rose-100/90">At Risk</p>
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(34,197,94,0.2)]">
                <div className="mb-4 flex items-center gap-2">
                  <Trophy className="h-4 w-4 text-emerald-300" />
                  <CardTitle className="text-white">Top Performers</CardTitle>
                </div>
                <div className="space-y-3">
                  {topPerformerCards.length === 0 ? <p className="text-sm text-slate-400">No top performer data.</p> : null}
                  {topPerformerCards.map((item) => {
                    const score = clampProgress(item.score);
                    return (
                      <div key={`${item.employee}-${item.score}`} className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-3 transition duration-300 hover:bg-emerald-500/15" title={`Score ${score}`}>
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-400/25 text-xs font-semibold text-emerald-100">{initials(item.employee)}</span>
                            <span className="text-sm font-medium text-slate-100">{item.employee}</span>
                          </div>
                          <span className="rounded-full border border-emerald-300/30 bg-emerald-300/20 px-2 py-0.5 text-xs font-semibold text-emerald-100">{score}</span>
                        </div>
                        <div className="mt-2 h-2 rounded-full bg-white/10">
                          <div className="h-2 rounded-full bg-emerald-400 transition-all duration-500" style={{ width: `${score}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <Card className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(239,68,68,0.2)]">
                <div className="mb-4 flex items-center gap-2">
                  <TrendingDown className="h-4 w-4 text-rose-300" />
                  <CardTitle className="text-white">Low Performers</CardTitle>
                </div>
                <div className="space-y-3">
                  {lowPerformerCards.length === 0 ? <p className="text-sm text-slate-400">No low performer data.</p> : null}
                  {lowPerformerCards.map((item) => {
                    const score = clampProgress(item.score);
                    return (
                      <div key={`${item.employee}-${item.score}`} className="rounded-xl border border-rose-400/20 bg-rose-500/10 p-3 transition duration-300 hover:bg-rose-500/15" title={`Score ${score}`}>
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-rose-400/25 text-xs font-semibold text-rose-100">{initials(item.employee)}</span>
                            <span className="text-sm font-medium text-slate-100">{item.employee}</span>
                          </div>
                          <span className="rounded-full border border-rose-300/30 bg-rose-300/20 px-2 py-0.5 text-xs font-semibold text-rose-100">{score}</span>
                        </div>
                        <div className="mt-2 h-2 rounded-full bg-white/10">
                          <div className="h-2 rounded-full bg-rose-400 transition-all duration-500" style={{ width: `${score}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(99,102,241,0.25)]">
                <CardTitle className="text-white">Workload Distribution</CardTitle>
                <CardDescription className="text-slate-400">Animated horizontal distribution by employee</CardDescription>
                <div className="mt-4 space-y-3">
                  {payload.workload_distribution.map((item) => {
                    const width = clampProgress((item.weightage / maxWorkload) * 100);
                    return (
                      <div key={`${item.employee}-${item.weightage}`} title={`${item.employee} ${item.weightage}%`}>
                        <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                          <span>{item.employee}</span>
                          <span>{item.weightage}%</span>
                        </div>
                        <div className="h-2.5 rounded-full bg-white/10">
                          <div
                            className="h-2.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-400 transition-all duration-700 ease-out"
                            style={{ width: `${width}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <Card className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(250,204,21,0.2)]">
                <CardTitle className="text-white">Rating Distribution</CardTitle>
                <CardDescription className="text-slate-400">Bucketed as 1-2, 3, and 4-5 ratings</CardDescription>
                <div className="mt-4 h-56">
                  <LazyPieChart data={donutData} innerRadius={55} outerRadius={86} tooltipStyle={chartTooltipStyle} />
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                  {donutData.map((entry) => (
                    <div key={entry.name} className="rounded-lg border border-white/10 bg-white/5 p-2 text-center" title={`${entry.value} ratings`}>
                      <span className="mx-auto mb-1 block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                      <p className="font-semibold text-slate-100">{entry.name}</p>
                      <p className="text-slate-400">{entry.value}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <Card className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(56,189,248,0.2)]">
              <CardTitle className="text-white">Team Members</CardTitle>
              <CardDescription className="text-slate-400">Color-coded table with progress, consistency, and health tags</CardDescription>
              <div className="mt-4 overflow-x-auto rounded-xl border border-white/10">
                <table className="w-full min-w-[760px] border-collapse">
                  <thead className="bg-white/5 text-left text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Name</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3">Progress</th>
                      <th className="px-4 py-3">Consistency</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payload.members.map((member) => {
                      const progress = clampProgress(member.progress);
                      const consistency = clampProgress(member.consistency);
                      return (
                        <tr key={member.id} className="border-t border-white/10 text-sm transition duration-300 hover:bg-white/5">
                          <td className="px-4 py-3 text-slate-100">
                            <div className="flex items-center gap-3">
                              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-sky-500/25 text-xs font-semibold text-sky-100">{initials(member.name)}</span>
                              <span className="font-medium">{member.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-slate-300">{member.role}</td>
                          <td className="px-4 py-3">
                            <div className="max-w-[220px]" title={`${progress}% progress`}>
                              <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                                <span>Progress</span>
                                <span>{progress}%</span>
                              </div>
                              <div className="h-2.5 rounded-full bg-white/10">
                                <div className="h-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500" style={{ width: `${progress}%` }} />
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className="inline-flex rounded-full border border-violet-300/30 bg-violet-500/15 px-2.5 py-1 text-xs font-semibold text-violet-200"
                              title="Consistency score"
                            >
                              {consistency}%
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(member.status)}`} title={`Status: ${statusLabel(member.status)}`}>
                              {statusLabel(member.status)}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
