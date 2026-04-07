"use client";

import { useCallback, useEffect, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { hrService } from "@/services/hr";
import type { HRMeeting, HRReportPayload } from "@/types";

function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const keys = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const header = keys.join(",");
  const body = rows.map((row) => keys.map((key) => `"${String(row[key] ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
  return `${header}\n${body}`;
}

export default function HRReportsPage() {
  const [reportType, setReportType] = useState<"employee" | "team" | "org">("org");
  const [report, setReport] = useState<HRReportPayload | null>(null);

  const [meetings, setMeetings] = useState<HRMeeting[]>([]);
  const [employeeFilter, setEmployeeFilter] = useState("");
  const [managerFilter, setManagerFilter] = useState("");
  const [transcriptByMeeting, setTranscriptByMeeting] = useState<Record<string, string>>({});

  const loadMeetings = useCallback(async () => {
    const data = await hrService.getMeetings({
      employee_id: employeeFilter || undefined,
      manager_id: managerFilter || undefined,
    });
    setMeetings(data);
  }, [employeeFilter, managerFilter]);

  useEffect(() => {
    loadMeetings().catch(() => null);
  }, [loadMeetings]);

  const generate = async () => {
    const payload = await hrService.getReport(reportType);
    setReport(payload);
  };

  const exportCsv = () => {
    if (!report) return;
    const csv = toCsv(report.rows || []);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `hr-${report.report_type}-report.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const exportPdf = () => {
    if (typeof window === "undefined") return;
    window.print();
  };

  const summarizeMeeting = async (meetingId: string) => {
    const transcript = (transcriptByMeeting[meetingId] || "").trim();
    if (!transcript) return;
    const response = await hrService.summarizeMeeting(meetingId, transcript);
    setMeetings((prev) => prev.map((meeting) => (meeting.id === meetingId ? { ...meeting, summary: response.summary } : meeting)));
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Reports</h1>
        <p className="text-sm text-muted-foreground">Generate employee/team/org reports and manage HR meeting summaries.</p>
      </div>

      <Card>
        <CardTitle>Report Generator</CardTitle>
        <CardDescription>Generate HR reports and export as CSV (PDF can be added with server-side renderer).</CardDescription>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <select
            className="h-10 rounded-md border border-input bg-card px-3 text-sm text-foreground"
            value={reportType}
            onChange={(event) => setReportType(event.target.value as "employee" | "team" | "org")}
          >
            <option value="employee">Employee report</option>
            <option value="team">Team report</option>
            <option value="org">Org report</option>
          </select>
          <Button onClick={() => generate().catch(() => null)}>Generate Report</Button>
          <Button variant="outline" onClick={exportCsv} disabled={!report}>Export CSV</Button>
          <Button variant="outline" onClick={exportPdf}>Export PDF</Button>
        </div>
        {report ? (
          <pre className="mt-4 max-h-72 overflow-auto rounded-md border border-border/70 bg-muted/30 p-3 text-xs">
            {JSON.stringify(report.rows.slice(0, 5), null, 2)}
          </pre>
        ) : null}
      </Card>

      <Card>
        <CardTitle>Meeting Tracking</CardTitle>
        <CardDescription>Filter HR-visible meetings by employee or manager, then generate AI summaries.</CardDescription>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <Input placeholder="Employee UUID" value={employeeFilter} onChange={(event) => setEmployeeFilter(event.target.value)} />
          <Input placeholder="Manager UUID" value={managerFilter} onChange={(event) => setManagerFilter(event.target.value)} />
          <Button variant="outline" onClick={() => loadMeetings().catch(() => null)}>Apply Filters</Button>
        </div>

        <div className="mt-4 space-y-3">
          {meetings.map((meeting) => (
            <div key={meeting.id} className="rounded-md border border-border/70 p-3">
              <p className="font-medium text-foreground">{meeting.employee_name || "Employee"} with {meeting.manager_name || "Manager"}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(meeting.start_time).toLocaleString()} - {new Date(meeting.end_time).toLocaleString()} · {meeting.status}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">Summary: {meeting.summary || "No summary yet"}</p>
              <Textarea
                className="mt-2"
                value={transcriptByMeeting[meeting.id] || ""}
                onChange={(event) => setTranscriptByMeeting((prev) => ({ ...prev, [meeting.id]: event.target.value }))}
                placeholder="Paste meeting transcript for AI summarization"
              />
              <Button size="sm" className="mt-2" onClick={() => summarizeMeeting(meeting.id).catch(() => null)}>Summarize with AI</Button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
