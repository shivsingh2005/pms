"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Download, FileBarChart2, FileSpreadsheet, FileText, Printer, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { hrService } from "@/services/hr";
import { useLeadershipPortalData } from "@/hooks/useLeadershipPortalData";
import { useSessionStore } from "@/store/useSessionStore";

type LeadershipReportType = "performance" | "attrition" | "training" | "manager-effectiveness";

interface ReportRow {
  [key: string]: string | number | boolean;
}

const REPORT_OPTIONS: Array<{ value: LeadershipReportType; label: string; description: string }> = [
  { value: "performance", label: "Performance Report", description: "Organization-wide performance trajectory and distribution." },
  { value: "attrition", label: "Attrition Risk Report", description: "Risk signals by employee and severity." },
  { value: "training", label: "Training Report", description: "Training demand and intervention priorities." },
  { value: "manager-effectiveness", label: "Manager Effectiveness Report", description: "Team quality by manager and readiness indicators." },
];

function downloadCsvFile(filename: string, csvContent: string) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportAsPrintablePdf(title: string, summary: Record<string, string | number>, rows: ReportRow[]) {
  const opened = window.open("", "_blank", "width=1100,height=900");
  if (!opened) return;

  const summaryHtml = Object.entries(summary)
    .map(([key, value]) => `<li><strong>${key}:</strong> ${String(value)}</li>`)
    .join("");

  const previewRows = rows.slice(0, 12);
  const headers = previewRows.length ? Object.keys(previewRows[0]) : [];
  const headerHtml = headers.map((header) => `<th style=\"padding:8px;border:1px solid #ddd;text-align:left;\">${header}</th>`).join("");
  const bodyHtml = previewRows
    .map((row) => `<tr>${headers.map((header) => `<td style=\"padding:8px;border:1px solid #ddd;\">${String(row[header] ?? "")}</td>`).join("")}</tr>`)
    .join("");

  opened.document.write(`
    <html>
      <head>
        <title>${title}</title>
      </head>
      <body style="font-family:Segoe UI, sans-serif; margin:24px; color:#111827;">
        <h1>${title}</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
        <h2>Summary</h2>
        <ul>${summaryHtml}</ul>
        <h2>Preview</h2>
        <table style="border-collapse:collapse;width:100%;font-size:13px;">
          <thead><tr>${headerHtml}</tr></thead>
          <tbody>${bodyHtml}</tbody>
        </table>
      </body>
    </html>
  `);
  opened.document.close();
  opened.focus();
  opened.print();
}

export default function LeadershipReportsPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  const {
    loading,
    emptyMessage,
    hasAnyData,
    topPerformers,
    atRiskEmployees,
    peopleInsights,
    summarySnapshot,
    toCsv,
    raw,
  } = useLeadershipPortalData({ range: "quarter" });

  const [reportType, setReportType] = useState<LeadershipReportType>("performance");
  const [generating, setGenerating] = useState(false);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [reportRows, setReportRows] = useState<ReportRow[]>([]);

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  const reportMeta = useMemo(() => {
    return REPORT_OPTIONS.find((option) => option.value === reportType) || REPORT_OPTIONS[0];
  }, [reportType]);

  const reportSummary = useMemo(() => {
    const base = {
      Employees: summarySnapshot.employees,
      Managers: summarySnapshot.managers,
      "At-Risk Employees": summarySnapshot.atRisk,
      Meetings: summarySnapshot.meetings,
      Goals: summarySnapshot.goals,
      "Check-ins": summarySnapshot.checkins,
      "Avg Performance": `${summarySnapshot.avgPerformance.toFixed(1)}%`,
    };

    if (reportType === "attrition") {
      return {
        ...base,
        "High Risk": atRiskEmployees.filter((entry) => entry.riskFlag === "High").length,
        "Medium Risk": atRiskEmployees.filter((entry) => entry.riskFlag === "Medium").length,
      };
    }

    if (reportType === "training") {
      return {
        ...base,
        "Training Needed": peopleInsights.filter((entry) => entry.needsTraining).length,
        "Ready Now": peopleInsights.filter((entry) => entry.promotionReadiness === "Ready Now").length,
      };
    }

    if (reportType === "manager-effectiveness") {
      const uniqueManagers = new Set(peopleInsights.map((entry) => entry.managerName || "Unassigned")).size;
      return {
        ...base,
        "Managers Evaluated": uniqueManagers,
        "Top Performer Pool": topPerformers.length,
      };
    }

    return {
      ...base,
      "Top Performers": topPerformers.length,
    };
  }, [atRiskEmployees, peopleInsights, reportType, summarySnapshot, topPerformers.length]);

  async function generateReport() {
    setGenerating(true);
    try {
      if (reportType === "performance") {
        const payload = await hrService.getReport("org").catch(() => null);
        const orgRow = (payload?.rows?.[0] as Record<string, unknown> | undefined) ?? null;
        const analytics = orgRow
          ? {
              performance_trend: Array.isArray(orgRow.performance_trend) ? orgRow.performance_trend : [],
              department_comparison: Array.isArray(orgRow.department_comparison) ? orgRow.department_comparison : [],
              rating_distribution: Array.isArray(orgRow.rating_distribution) ? orgRow.rating_distribution : [],
              checkin_consistency: Array.isArray(orgRow.checkin_consistency) ? orgRow.checkin_consistency : [],
            }
          : raw.orgAnalytics;

        const rows: ReportRow[] = [
          ...((analytics?.performance_trend as Array<Record<string, unknown>> | undefined) ?? []).map((item, index) => ({
            row: index + 1,
            metric: "performance_trend",
            period: String(item.week ?? ""),
            value: Number(item.value ?? 0),
          })),
          ...((analytics?.department_comparison as Array<Record<string, unknown>> | undefined) ?? []).map((item, index) => ({
            row: index + 1,
            metric: "department_comparison",
            period: String(item.department ?? ""),
            value: Number(item.value ?? 0),
          })),
          ...((analytics?.rating_distribution as Array<Record<string, unknown>> | undefined) ?? []).map((item, index) => ({
            row: index + 1,
            metric: "rating_distribution",
            period: String(item.label ?? ""),
            value: Number(item.count ?? 0),
          })),
          ...((analytics?.checkin_consistency as Array<Record<string, unknown>> | undefined) ?? []).map((item, index) => ({
            row: index + 1,
            metric: "checkin_consistency",
            period: String(item.week ?? ""),
            value: Number(item.value ?? 0),
          })),
        ];
        setReportRows(rows);
      }

      if (reportType === "attrition") {
        setReportRows(
          atRiskEmployees.map((employee, index) => ({
            row: index + 1,
            name: employee.name,
            role: employee.role,
            risk: employee.riskFlag,
            rating: employee.rating,
            progress: employee.progress,
            consistency: employee.consistency,
          })),
        );
      }

      if (reportType === "training") {
        const rows = peopleInsights
          .filter((employee) => employee.needsTraining)
          .map((employee, index) => ({
            row: index + 1,
            name: employee.name,
            role: employee.role,
            rating: employee.rating,
            progress: employee.progress,
            consistency: employee.consistency,
            readiness: employee.promotionReadiness,
          }));
        setReportRows(rows);
      }

      if (reportType === "manager-effectiveness") {
        const managerScore = new Map<string, number[]>();
        for (const person of peopleInsights) {
          const key = person.managerName || "Unassigned";
          const score = (person.progress * 0.45) + (person.consistency * 0.25) + (person.rating * 20 * 0.3);
          managerScore.set(key, [...(managerScore.get(key) ?? []), score]);
        }
        const rows = Array.from(managerScore.entries()).map(([manager, scores], index) => ({
          row: index + 1,
          manager,
          team_size: scores.length,
          avg_team_score: Number((scores.reduce((sum, current) => sum + current, 0) / scores.length).toFixed(1)),
        }));
        setReportRows(rows);
      }

      setGeneratedAt(new Date().toLocaleString());
    } finally {
      setGenerating(false);
    }
  }

  function exportCsv() {
    const csv = toCsv(reportRows);
    if (!csv) return;
    downloadCsvFile(`${reportType}-report.csv`, csv);
  }

  function exportPdf() {
    exportAsPrintablePdf(reportMeta.label, reportSummary, reportRows);
  }

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Reports</h1>
        <p className="text-sm text-muted-foreground">Generate executive-ready reports with preview and export workflows.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Skeleton className="h-64 w-full rounded-2xl bg-white/5" />
          <Skeleton className="h-64 w-full rounded-2xl bg-white/5" />
        </div>
      ) : !hasAnyData ? (
        <Card className="rounded-2xl border border-dashed border-border/80 bg-card/70 text-center">
          <CardTitle>Reporting Data Unavailable</CardTitle>
          <CardDescription className="mt-2">{emptyMessage}</CardDescription>
        </Card>
      ) : (
        <>
          <Card className="rounded-2xl border border-border/75 bg-gradient-to-r from-blue-500/10 via-emerald-500/10 to-amber-500/10">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div className="space-y-2">
                <CardTitle>Generate Reports</CardTitle>
                <CardDescription>{reportMeta.description}</CardDescription>
                <select
                  value={reportType}
                  onChange={(event) => setReportType(event.target.value as LeadershipReportType)}
                  className="h-10 rounded-lg border border-border/70 bg-card px-3 text-sm text-foreground"
                >
                  {REPORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={generateReport} disabled={generating}>
                  <FileBarChart2 className="mr-2 h-4 w-4" />
                  {generating ? "Generating..." : "Generate"}
                </Button>
                <Button variant="outline" onClick={exportCsv} disabled={!reportRows.length}>
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
                <Button variant="outline" onClick={exportPdf} disabled={!reportRows.length}>
                  <Printer className="mr-2 h-4 w-4" />
                  Export PDF
                </Button>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <CardTitle>Summary Preview</CardTitle>
              <CardDescription>{generatedAt ? `Generated at ${generatedAt}` : "Generate a report to preview live summary."}</CardDescription>
              <div className="mt-4 grid grid-cols-1 gap-2">
                {Object.entries(reportSummary).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-lg border border-border/70 bg-surface/80 px-3 py-2 text-sm">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-semibold text-foreground">{String(value)}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="rounded-2xl border border-border/75 bg-card/95">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-600" />
                <CardTitle>Export Options</CardTitle>
              </div>
              <CardDescription>Download as CSV or print-ready PDF format for leadership reviews.</CardDescription>
              <div className="mt-4 space-y-3">
                <div className="rounded-xl border border-border/70 bg-surface/75 p-3">
                  <p className="text-sm font-medium text-foreground">CSV Export</p>
                  <p className="text-xs text-muted-foreground">Structured rows for spreadsheet analysis.</p>
                </div>
                <div className="rounded-xl border border-border/70 bg-surface/75 p-3">
                  <p className="text-sm font-medium text-foreground">PDF Export</p>
                  <p className="text-xs text-muted-foreground">Print-friendly executive snapshot with summary and preview rows.</p>
                </div>
              </div>
            </Card>
          </div>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Report Preview Rows</CardTitle>
              <div className="text-xs text-muted-foreground">Showing first {Math.min(reportRows.length, 10)} of {reportRows.length}</div>
            </div>

            {!reportRows.length ? (
              <CardDescription className="mt-4">Generate a report to see preview rows before export.</CardDescription>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-xl border border-border/70">
                <table className="w-full min-w-[720px] border-collapse text-sm">
                  <thead className="bg-surface/80">
                    <tr>
                      {Object.keys(reportRows[0]).map((key) => (
                        <th key={key} className="border-b border-border/70 px-3 py-2 text-left font-semibold text-foreground">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reportRows.slice(0, 10).map((row, index) => (
                      <tr key={`report-preview-row-${index}`} className="odd:bg-card even:bg-surface/40">
                        {Object.entries(row).map(([key, value]) => (
                          <td key={`${key}-${index}`} className="border-b border-border/50 px-3 py-2 text-muted-foreground">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="outline" onClick={exportCsv} disabled={!reportRows.length}>
                <Download className="mr-2 h-4 w-4" />
                Download CSV
              </Button>
              <Button variant="outline" onClick={exportPdf} disabled={!reportRows.length}>
                <FileText className="mr-2 h-4 w-4" />
                Print to PDF
              </Button>
            </div>
          </Card>
        </>
      )}
    </motion.div>
  );
}
