"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { dashboardService, type DashboardOverview } from "@/services/dashboard";
import { checkinsService } from "@/services/checkins";
import { hrService } from "@/services/hr";
import type { HREmployeeDirectoryItem, HRManagerOption, HRMeeting, HROrgAnalytics, HROverview } from "@/types";

export type LeadershipTimeRange = "week" | "month" | "quarter";

export interface LeadershipFilters {
  range: LeadershipTimeRange;
  department?: string;
  managerId?: string;
}

export interface LeadershipPersonInsight {
  id: string;
  name: string;
  role: string;
  rating: number;
  progress: number;
  consistency: number;
  riskFlag: "Low" | "Medium" | "High";
  needsTraining: boolean;
  promotionReadiness: "Ready Now" | "Ready in 1-2 cycles" | "Needs Development";
  managerName?: string | null;
}

interface LeadershipDataState {
  overview: DashboardOverview | null;
  hrOverview: HROverview | null;
  orgAnalytics: HROrgAnalytics | null;
  employees: HREmployeeDirectoryItem[];
  managers: HRManagerOption[];
  meetings: HRMeeting[];
  ratedCheckinsCount: number;
}

const EMPTY_MESSAGE = "Data is being prepared. Please check back soon.";

const RANGE_POINTS: Record<LeadershipTimeRange, number> = {
  week: 4,
  month: 8,
  quarter: 13,
};

function toPercent(value: number) {
  return Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
}

function average(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((sum, current) => sum + current, 0) / values.length;
}

function formatDateLabel(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function sliceByRange<T>(rows: T[], range: LeadershipTimeRange) {
  const size = RANGE_POINTS[range];
  return rows.length > size ? rows.slice(rows.length - size) : rows;
}

function riskBand(entry: { progress: number; consistency: number; rating: number }) {
  if (entry.progress < 45 || entry.consistency < 55 || entry.rating <= 2.1) return "High";
  if (entry.progress < 65 || entry.consistency < 70 || entry.rating <= 3.2) return "Medium";
  return "Low";
}

function promotionReadiness(entry: { progress: number; consistency: number; rating: number; needsTraining: boolean }) {
  const score = (entry.progress * 0.45) + (entry.consistency * 0.25) + (entry.rating * 20 * 0.3);
  if (score >= 80 && !entry.needsTraining) return "Ready Now";
  if (score >= 65) return "Ready in 1-2 cycles";
  return "Needs Development";
}

function finalRatingFromRecords(base: HREmployeeDirectoryItem, finalRating?: { average_rating: number; ratings_count: number }) {
  if (finalRating && finalRating.ratings_count > 0) {
    return Number(finalRating.average_rating.toFixed(2));
  }
  return 0;
}

function buildCsv(rows: Record<string, unknown>[]) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escapeValue = (value: unknown) => {
    const text = String(value ?? "");
    if (text.includes(",") || text.includes("\n") || text.includes('"')) {
      return `"${text.replaceAll('"', '""')}"`;
    }
    return text;
  };

  const lines = [headers.join(",")];
  for (const row of rows) {
    lines.push(headers.map((header) => escapeValue(row[header])).join(","));
  }
  return lines.join("\n");
}

export function useLeadershipPortalData(filters: LeadershipFilters) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<LeadershipDataState>({
    overview: null,
    hrOverview: null,
    orgAnalytics: null,
    employees: [],
    managers: [],
    meetings: [],
    ratedCheckinsCount: 0,
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [overview, hrOverview] = await Promise.all([
        dashboardService.getOverview().catch(() => null),
        hrService.getOverview().catch(() => null),
      ]);

      const employees = await hrService
        .getEmployees({
          department: filters.department || undefined,
          manager_id: filters.managerId || undefined,
        })
        .catch(() => []);
      setState({
        overview,
        hrOverview,
        orgAnalytics: null,
        employees,
        managers: [],
        meetings: [],
        ratedCheckinsCount: 0,
      });

      setLoading(false);

      Promise.all([
        hrService.getOrgAnalytics().catch(() => null),
        hrService.getManagers(filters.department).catch(() => []),
        hrService.getMeetings(filters.managerId ? { manager_id: filters.managerId } : undefined).catch(() => []),
        (async () => {
          let scopedEmployees = employees;
          if (filters.managerId) {
            const teamRows = await hrService
              .getTeamByManager(filters.managerId, { department: filters.department || undefined })
              .catch(() => []);

            if (teamRows.length) {
              const teamById = new Map(teamRows.map((member) => [member.id, member]));
              scopedEmployees = employees
                .filter((entry) => teamById.has(entry.id))
                .map((entry) => {
                  const team = teamById.get(entry.id);
                  return {
                    ...entry,
                    progress: team?.progress ?? entry.progress,
                    consistency: team?.consistency ?? entry.consistency,
                    rating: team?.rating ?? entry.rating,
                  };
                });
            }
          }

          const finalRatings = new Map<string, { average_rating: number; ratings_count: number }>();
          const ratings = await checkinsService.getFinalRatingsBulk(scopedEmployees.map((employee) => employee.id)).catch(() => []);
          for (const rating of ratings) {
            finalRatings.set(rating.employee_id, rating);
          }

          const employeesWithFinalRatings = scopedEmployees.map((employee) => ({
            ...employee,
            rating: finalRatingFromRecords(employee, finalRatings.get(employee.id)),
          }));
          const ratedCheckinsCount = Array.from(finalRatings.values()).reduce((sum, item) => sum + item.ratings_count, 0);

          return { employeesWithFinalRatings, ratedCheckinsCount };
        })(),
      ]).then(([orgAnalytics, managers, meetings, ratingsPayload]) => {
        setState((prev) => ({
          ...prev,
          orgAnalytics,
          managers,
          meetings,
          employees: ratingsPayload.employeesWithFinalRatings,
          ratedCheckinsCount: ratingsPayload.ratedCheckinsCount,
        }));
      });
    } catch {
      setError("Unable to load leadership insights right now.");
      setLoading(false);
    }
  }, [filters.department, filters.managerId]);

  useEffect(() => {
    void load();
  }, [load]);

  const departments = useMemo(() => {
    const set = new Set(state.employees.map((employee) => employee.department).filter(Boolean));
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [state.employees]);

  const peopleInsights = useMemo<LeadershipPersonInsight[]>(() => {
    return state.employees.map((employee) => {
      const rating = Number(employee.rating ?? 0);
      const progress = toPercent(employee.progress);
      const consistency = toPercent(employee.consistency);
      const riskFlag = riskBand({ progress, consistency, rating });
      const needsTraining = Boolean(employee.needs_training);
      return {
        id: employee.id,
        name: employee.name,
        role: employee.role,
        rating,
        progress,
        consistency,
        riskFlag,
        needsTraining,
        promotionReadiness: promotionReadiness({ progress, consistency, rating, needsTraining }),
        managerName: employee.manager_name,
      };
    });
  }, [state.employees]);

  const topPerformers = useMemo(() => {
    return [...peopleInsights]
      .sort((a, b) => ((b.progress * 0.45) + (b.consistency * 0.25) + (b.rating * 20 * 0.3)) - ((a.progress * 0.45) + (a.consistency * 0.25) + (a.rating * 20 * 0.3)))
      .slice(0, 5);
  }, [peopleInsights]);

  const atRiskEmployees = useMemo(() => {
    return peopleInsights
      .filter((employee) => employee.riskFlag !== "Low")
      .sort((a, b) => {
        const riskWeight = { High: 2, Medium: 1, Low: 0 } as const;
        return riskWeight[b.riskFlag] - riskWeight[a.riskFlag];
      })
      .slice(0, 8);
  }, [peopleInsights]);

  const orgProgressTrend = useMemo(() => {
    const rows = state.orgAnalytics?.performance_trend ?? [];
    const shaped = rows.length
      ? rows.map((row) => ({
          period: formatDateLabel(String(row.week)),
          value: Number(row.value ?? 0),
        }))
      : (state.overview?.trend ?? []).map((row) => ({
          period: String(row.name),
          value: Number(row.score ?? 0),
        }));
    return sliceByRange(shaped, filters.range);
  }, [filters.range, state.orgAnalytics, state.overview]);

  const checkinFrequencyTrend = useMemo(() => {
    const rows = state.orgAnalytics?.checkin_consistency ?? [];
    const shaped = rows.length
      ? rows.map((row) => ({
          period: formatDateLabel(String(row.week)),
          value: Number(row.value ?? 0),
        }))
      : (state.overview?.velocity ?? []).map((row) => ({
          period: String(row.name),
          value: Number(row.score ?? 0),
        }));
    return sliceByRange(shaped, filters.range);
  }, [filters.range, state.orgAnalytics, state.overview]);

  const underperformingTrend = useMemo(() => {
    return orgProgressTrend.map((row) => ({
      period: row.period,
      value: Number(Math.max(0, 70 - row.value).toFixed(1)),
    }));
  }, [orgProgressTrend]);

  const departmentComparison = useMemo(() => {
    const rows = (state.orgAnalytics?.department_comparison ?? []).map((row) => ({
      department: String(row.department),
      value: Number(row.value ?? 0),
    }));
    if (rows.length) {
      return rows;
    }

    const buckets = new Map<string, { sum: number; count: number }>();
    for (const employee of state.employees) {
      const key = employee.department || "General";
      const current = buckets.get(key) ?? { sum: 0, count: 0 };
      buckets.set(key, { sum: current.sum + Number(employee.progress ?? 0), count: current.count + 1 });
    }

    return Array.from(buckets.entries()).map(([department, value]) => ({
      department,
      value: value.count ? Number((value.sum / value.count).toFixed(1)) : 0,
    }));
  }, [state.employees, state.orgAnalytics]);

  const riskDistribution = useMemo(() => {
    const counts = { Low: 0, Medium: 0, High: 0 };
    for (const person of peopleInsights) {
      counts[person.riskFlag] += 1;
    }
    return [
      { name: "Low Risk", value: counts.Low },
      { name: "Medium Risk", value: counts.Medium },
      { name: "High Risk", value: counts.High },
    ];
  }, [peopleInsights]);

  const talentDistribution = useMemo(() => {
    const buckets = {
      "4.5 - 5.0": 0,
      "3.5 - 4.49": 0,
      "2.5 - 3.49": 0,
      "0 - 2.49": 0,
    };

    for (const person of peopleInsights) {
      if (person.rating >= 4.5) buckets["4.5 - 5.0"] += 1;
      else if (person.rating >= 3.5) buckets["3.5 - 4.49"] += 1;
      else if (person.rating >= 2.5) buckets["2.5 - 3.49"] += 1;
      else buckets["0 - 2.49"] += 1;
    }

    return Object.entries(buckets).map(([band, count]) => ({ band, count }));
  }, [peopleInsights]);

  const trainingNeedSummary = useMemo(() => {
    const rows = state.hrOverview?.training_heatmap ?? [];
    const summary = new Map<string, number>();
    for (const item of rows) {
      summary.set(item.training_need_level, (summary.get(item.training_need_level) ?? 0) + 1);
    }

    const ordered = ["No Need", "Low", "Medium", "High", "Critical"];
    return ordered.map((label) => ({ label, value: summary.get(label) ?? 0 }));
  }, [state.hrOverview]);

  const goalCompletionRate = useMemo(() => {
    if (state.overview?.kpi.cycle_completion !== undefined) {
      return toPercent(state.overview.kpi.cycle_completion);
    }

    const totalGoals = Number(state.overview?.kpi.total_goals ?? 0);
    const completedGoals = Number(state.overview?.kpi.goals_completed ?? 0);
    return totalGoals > 0 ? toPercent((completedGoals / totalGoals) * 100) : 0;
  }, [state.overview]);

  const aiInsights = useMemo(() => {
    const latest = orgProgressTrend[orgProgressTrend.length - 1]?.value ?? 0;
    const previous = orgProgressTrend[orgProgressTrend.length - 2]?.value ?? latest;
    const delta = latest - previous;
    const direction = delta < 0 ? "dropped" : "improved";

    const attritionRiskCount = atRiskEmployees.filter((employee) => employee.riskFlag === "High").length;

    const managerRows = new Map<string, number[]>();
    for (const person of peopleInsights) {
      const key = person.managerName || "Unassigned";
      const score = (person.progress * 0.45) + (person.consistency * 0.25) + (person.rating * 20 * 0.3);
      managerRows.set(key, [...(managerRows.get(key) ?? []), score]);
    }

    const bestManager = Array.from(managerRows.entries())
      .map(([name, scores]) => ({ name, score: average(scores) }))
      .sort((a, b) => b.score - a.score)[0];

    return [
      `Performance ${direction} by ${Math.abs(delta).toFixed(1)}% in the latest period.`,
      `${attritionRiskCount} employees are in high attrition risk band.`,
      `${bestManager ? `${bestManager.name} team is performing best.` : "Manager effectiveness will appear as team data increases."}`,
      "Final rating follows check-in -> approved meeting -> manager rating, displayed as average of all recorded check-in ratings.",
    ];
  }, [atRiskEmployees, orgProgressTrend, peopleInsights]);

  const hasAnyData = useMemo(() => {
    return Boolean(
      state.employees.length ||
      state.managers.length ||
      state.meetings.length ||
      state.hrOverview?.training_heatmap.length ||
      state.orgAnalytics?.performance_trend.length ||
      state.overview ||
      state.hrOverview,
    );
  }, [state]);

  const summarySnapshot = useMemo(() => {
    return {
      employees: state.hrOverview?.total_employees ?? state.employees.length,
      managers: state.hrOverview?.total_managers ?? state.managers.length,
      atRisk: state.hrOverview?.at_risk_employees ?? atRiskEmployees.length,
      meetings: state.meetings.length,
      goals: Number(state.overview?.kpi.total_goals ?? 0),
      checkins: state.ratedCheckinsCount,
      avgPerformance: Number(state.hrOverview?.avg_org_performance ?? state.overview?.kpi.org_health ?? 0),
    };
  }, [atRiskEmployees.length, state]);

  const toCsv = useCallback((rows: Record<string, unknown>[]) => buildCsv(rows), []);

  return {
    loading,
    error,
    emptyMessage: EMPTY_MESSAGE,
    hasAnyData,
    departments,
    managers: state.managers,
    peopleInsights,
    topPerformers,
    atRiskEmployees,
    orgProgressTrend,
    departmentComparison,
    underperformingTrend,
    checkinFrequencyTrend,
    riskDistribution,
    talentDistribution,
    trainingNeedSummary,
    goalCompletionRate,
    aiInsights,
    summarySnapshot,
    raw: state,
    reload: load,
    toCsv,
  };
}
