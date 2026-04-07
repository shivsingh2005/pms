"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CalendarDays, CircleCheckBig, Clock3, ExternalLink, List, Plus, TriangleAlert, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { authService } from "@/services/auth";
import { hrService } from "@/services/hr";
import type { HREmployeeDirectoryItem, HRManagerOption, HRMeeting } from "@/types";
import { toast } from "sonner";

type MeetingView = "list" | "calendar";
type StatusFilter = "all" | "normal" | "completed" | "missed" | "pending";

interface ScheduleFormState {
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  additional_participants: string;
}

interface SelectableParticipant {
  id: string;
  label: string;
  email: string;
  kind: "employee" | "manager";
}

const INITIAL_FORM: ScheduleFormState = {
  title: "",
  description: "",
  start_time: "",
  end_time: "",
  additional_participants: "",
};

function isPastMeeting(meeting: HRMeeting): boolean {
  return new Date(meeting.end_time).getTime() < Date.now();
}

function lifecycleStatus(meeting: HRMeeting): "normal" | "completed" | "missed" | "pending" {
  if (meeting.status === "completed") return "completed";
  if (meeting.status === "cancelled") return "missed";
  if (meeting.status === "scheduled" && isPastMeeting(meeting)) return "missed";
  if (meeting.created_from_checkin) return "pending";
  return "normal";
}

function statusBadgeClass(status: ReturnType<typeof lifecycleStatus>): string {
  if (status === "completed") return "border-success/30 bg-success/15 text-success";
  if (status === "missed") return "border-error/30 bg-error/15 text-error";
  if (status === "pending") return "border-warning/35 bg-warning/20 text-warning";
  return "border-primary/30 bg-primary/15 text-primary";
}

function statusText(status: ReturnType<typeof lifecycleStatus>): string {
  if (status === "completed") return "Completed";
  if (status === "missed") return "Missed";
  if (status === "pending") return "Pending";
  return "Normal";
}

function dayLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { weekday: "short" });
}

export default function HRMeetingsPage() {
  const router = useRouter();
  const [meetings, setMeetings] = useState<HRMeeting[]>([]);
  const [employees, setEmployees] = useState<HREmployeeDirectoryItem[]>([]);
  const [managers, setManagers] = useState<HRManagerOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null);

  const [view, setView] = useState<MeetingView>("list");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [employeeFilter, setEmployeeFilter] = useState("all");
  const [managerFilter, setManagerFilter] = useState("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [summaryOpenFor, setSummaryOpenFor] = useState<string | null>(null);
  const [rescheduleOpenFor, setRescheduleOpenFor] = useState<HRMeeting | null>(null);
  const [detailOpenFor, setDetailOpenFor] = useState<HRMeeting | null>(null);

  const [scheduleForm, setScheduleForm] = useState<ScheduleFormState>(INITIAL_FORM);
  const [transcriptByMeeting, setTranscriptByMeeting] = useState<Record<string, string>>({});
  const [includeAllEmployees, setIncludeAllEmployees] = useState(false);
  const [includeAllManagers, setIncludeAllManagers] = useState(false);
  const [includeTeamMembers, setIncludeTeamMembers] = useState(false);
  const [teamManagerId, setTeamManagerId] = useState("");
  const [selectedParticipantEmails, setSelectedParticipantEmails] = useState<string[]>([]);

  const [calendarMonth, setCalendarMonth] = useState<Date>(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [meetingRows, employeeRows, managerRows] = await Promise.all([
        hrService.getMeetings(),
        hrService.getEmployees(),
        hrService.getManagers(),
      ]);
      setMeetings(meetingRows);
      setEmployees(employeeRows);
      setManagers(managerRows);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData().catch(() => null);
  }, [loadData]);

  useEffect(() => {
    authService
      .getGoogleConnectionStatus()
      .then((status) => setGoogleConnected(status.connected))
      .catch(() => setGoogleConnected(null));
  }, []);

  const refreshGoogleStatus = useCallback(async () => {
    const status = await authService.getGoogleConnectionStatus();
    setGoogleConnected(status.connected);
    return status.connected;
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(typeof window === "undefined" ? "" : window.location.search);
    const connected = params.get("google_connected");
    const reason = params.get("reason");
    if (!connected && !reason) return;
    if (connected === "1") {
      setGoogleConnected(true);
      toast.success("Google Calendar connected");
    } else {
      setGoogleConnected(false);
      toast.error(`Google connection failed${reason ? `: ${reason.replaceAll("_", " ")}` : ""}`);
    }
    router.replace("/hr/meetings");
  }, [router]);

  const allEmployeeParticipants = useMemo(
    () =>
      employees
        .filter((employee) => Boolean(employee.email))
        .map((employee) => ({ id: employee.id, label: employee.name, email: String(employee.email).trim().toLowerCase(), kind: "employee" as const })),
    [employees],
  );

  const allManagerParticipants = useMemo(
    () =>
      managers
        .filter((manager) => Boolean(manager.email))
        .map((manager) => ({ id: manager.id, label: manager.name, email: String(manager.email).trim().toLowerCase(), kind: "manager" as const })),
    [managers],
  );

  const selectedTeamMembers = useMemo(() => {
    const manager = managers.find((item) => item.id === teamManagerId);
    if (!manager) return [] as SelectableParticipant[];
    return employees
      .filter((employee) => employee.manager_name === manager.name && employee.email)
      .map((employee) => ({ id: employee.id, label: employee.name, email: String(employee.email).trim().toLowerCase(), kind: "employee" as const }));
  }, [employees, managers, teamManagerId]);

  const selectableParticipants = useMemo(() => {
    const deduped = new Map<string, SelectableParticipant>();
    [...allManagerParticipants, ...allEmployeeParticipants].forEach((participant) => deduped.set(participant.email, participant));
    return Array.from(deduped.values());
  }, [allEmployeeParticipants, allManagerParticipants]);

  const participantLabelByEmail = useMemo(() => {
    const map = new Map<string, string>();
    selectableParticipants.forEach((participant) => map.set(participant.email, participant.label));
    return map;
  }, [selectableParticipants]);

  const participantGroups = useMemo(() => {
    const groups: string[] = [];
    if (includeAllEmployees) groups.push("All Employees");
    if (includeAllManagers) groups.push("All Managers");
    if (includeTeamMembers && teamManagerId) {
      const managerName = managers.find((manager) => manager.id === teamManagerId)?.name;
      groups.push(managerName ? `Team: ${managerName}` : "Team Selection");
    }
    return groups;
  }, [includeAllEmployees, includeAllManagers, includeTeamMembers, managers, teamManagerId]);

  const participantPreview = useMemo(() => {
    const manual = scheduleForm.additional_participants
      .split(",")
      .map((entry) => entry.trim().toLowerCase())
      .filter(Boolean);

    const grouped = [
      ...(includeAllEmployees ? allEmployeeParticipants.map((item) => item.email) : []),
      ...(includeAllManagers ? allManagerParticipants.map((item) => item.email) : []),
      ...(includeTeamMembers ? selectedTeamMembers.map((item) => item.email) : []),
    ];

    return Array.from(new Set([...selectedParticipantEmails, ...grouped, ...manual]));
  }, [
    allEmployeeParticipants,
    allManagerParticipants,
    includeAllEmployees,
    includeAllManagers,
    includeTeamMembers,
    scheduleForm.additional_participants,
    selectedParticipantEmails,
    selectedTeamMembers,
  ]);

  const participantChips = useMemo(() => {
    const individualChips = participantPreview.slice(0, 8).map((email) => participantLabelByEmail.get(email) || email);
    return [...participantGroups, ...individualChips];
  }, [participantGroups, participantPreview, participantLabelByEmail]);

  const participantCountLabel = `${participantPreview.length} participant${participantPreview.length === 1 ? "" : "s"} selected`;

  const rescheduleParticipantList = useMemo(
    () =>
      scheduleForm.additional_participants
        .split(",")
        .map((entry) => entry.trim().toLowerCase())
        .filter(Boolean),
    [scheduleForm.additional_participants],
  );

  const toggleIndividualParticipant = (email: string) => {
    setSelectedParticipantEmails((prev) => (prev.includes(email) ? prev.filter((entry) => entry !== email) : [...prev, email]));
  };

  const resetSchedulerSelection = () => {
    setScheduleForm(INITIAL_FORM);
    setIncludeAllEmployees(false);
    setIncludeAllManagers(false);
    setIncludeTeamMembers(false);
    setTeamManagerId("");
    setSelectedParticipantEmails([]);
  };

  const connectGoogleCalendar = useCallback(async () => {
    try {
      const { authorization_url } = await authService.getGoogleAuthorizeUrl("/hr/meetings");
      if (!authorization_url) {
        toast.error("Google OAuth is not configured on backend");
        return;
      }
      window.location.href = authorization_url;
    } catch {
      toast.error("Failed to initialize Google OAuth flow");
    }
  }, []);

  const filteredMeetings = useMemo(() => {
    return meetings.filter((meeting) => {
      if (employeeFilter !== "all" && meeting.employee_id !== employeeFilter) return false;
      if (managerFilter !== "all" && meeting.manager_id !== managerFilter) return false;

      const meetingStart = new Date(meeting.start_time);
      if (fromDate) {
        const from = new Date(`${fromDate}T00:00:00`);
        if (meetingStart < from) return false;
      }
      if (toDate) {
        const to = new Date(`${toDate}T23:59:59`);
        if (meetingStart > to) return false;
      }

      if (statusFilter !== "all" && lifecycleStatus(meeting) !== statusFilter) return false;
      return true;
    });
  }, [employeeFilter, fromDate, managerFilter, meetings, statusFilter, toDate]);

  const metrics = useMemo(() => {
    const completed = filteredMeetings.filter((meeting) => lifecycleStatus(meeting) === "completed").length;
    const pending = filteredMeetings.filter((meeting) => lifecycleStatus(meeting) === "pending").length;
    const missed = filteredMeetings.filter((meeting) => lifecycleStatus(meeting) === "missed").length;
    const summarized = filteredMeetings.filter((meeting) => Boolean(meeting.summary && meeting.summary.trim())).length;
    return {
      total: filteredMeetings.length,
      completed,
      pending,
      missed,
      summarized,
    };
  }, [filteredMeetings]);

  const scheduleMeeting = async () => {
    if (!scheduleForm.start_time || !scheduleForm.end_time) {
      toast.error("Start time and end time are required");
      return;
    }

    const start = new Date(scheduleForm.start_time);
    const end = new Date(scheduleForm.end_time);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
      toast.error("Please provide a valid meeting time range");
      return;
    }

    if (participantPreview.length === 0) {
      toast.error("At least 1 participant is required");
      return;
    }

    let isConnected = false;
    try {
      isConnected = await refreshGoogleStatus();
    } catch {
      isConnected = false;
    }

    if (!isConnected) {
      toast.error("Connect Google Calendar first to generate Meet link and send invites");
      return;
    }

    setSaving(true);
    try {
      await hrService.createMeeting({
        title: scheduleForm.title.trim() || "HR Meeting",
        meeting_type: "HR",
        description: scheduleForm.description || undefined,
        manager_id: teamManagerId || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        participants: participantPreview,
      });
      setScheduleOpen(false);
      resetSchedulerSelection();
      await loadData();
      toast.success("Meeting created with Google Meet link and invites sent");
    } catch {
      toast.error("Unable to create meeting. Check Google connection and required fields.");
    } finally {
      setSaving(false);
    }
  };

  const rescheduleMeeting = async () => {
    if (!rescheduleOpenFor) return;
    const start = new Date(scheduleForm.start_time);
    const end = new Date(scheduleForm.end_time);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
      toast.error("Provide a valid start and end time");
      return;
    }

    setSaving(true);
    try {
      await hrService.updateMeeting(rescheduleOpenFor.id, {
        title: scheduleForm.title || undefined,
        description: scheduleForm.description || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        participants: rescheduleParticipantList,
      });
      setRescheduleOpenFor(null);
      await loadData();
      toast.success("Meeting updated and Google Calendar synced");
    } catch {
      toast.error("Unable to update meeting");
    } finally {
      setSaving(false);
    }
  };

  const cancelMeeting = async (meetingId: string) => {
    setSaving(true);
    try {
      await hrService.cancelMeeting(meetingId);
      await loadData();
      toast.success("Meeting cancelled");
    } catch {
      toast.error("Unable to cancel meeting");
    } finally {
      setSaving(false);
    }
  };

  const summarizeMeeting = async (meetingId: string) => {
    const transcript = (transcriptByMeeting[meetingId] || "").trim();
    if (!transcript) return;
    setSaving(true);
    try {
      const response = await hrService.summarizeMeeting(meetingId, transcript);
      setMeetings((prev) => prev.map((meeting) => (meeting.id === meetingId ? { ...meeting, summary: response.summary } : meeting)));
      toast.success("AI summary generated");
    } catch {
      toast.error("Unable to generate summary");
    } finally {
      setSaving(false);
    }
  };

  const monthDays = useMemo(() => {
    const firstDay = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
    const lastDay = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 0);
    const days: Date[] = [];
    const cursor = new Date(firstDay);
    while (cursor <= lastDay) {
      days.push(new Date(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }
    return days;
  }, [calendarMonth]);

  const meetingsByDate = useMemo(() => {
    const map = new Map<string, HRMeeting[]>();
    filteredMeetings.forEach((meeting) => {
      const day = new Date(meeting.start_time).toISOString().slice(0, 10);
      const current = map.get(day) || [];
      current.push(meeting);
      map.set(day, current);
    });
    return map;
  }, [filteredMeetings]);

  return (
    <motion.div className="space-y-6" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: "easeOut" }}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-foreground">HR Meetings Control Center</h1>
          <p className="text-sm text-muted-foreground">Unified meeting scheduler with Google Meet links, participant invites, and organization-wide visibility.</p>
        </div>
        <div className="flex items-center gap-2">
          {googleConnected !== null && (
            <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${googleConnected ? "bg-success/15 text-success" : "bg-warning/15 text-warning"}`}>
              {googleConnected ? "Google connected" : "Google not connected"}
            </span>
          )}
          {!googleConnected ? <Button variant="outline" onClick={() => connectGoogleCalendar().catch(() => null)}>Connect Google Calendar</Button> : null}
          <Button onClick={() => {
            resetSchedulerSelection();
            setScheduleOpen(true);
          }}>
            <Plus className="mr-2 h-4 w-4" /> Schedule Meeting
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card><CardTitle>Total Meetings</CardTitle><CardDescription>{metrics.total}</CardDescription></Card>
        <Card><CardTitle>Completed Meetings</CardTitle><CardDescription>{metrics.completed}</CardDescription></Card>
        <Card><CardTitle>Pending Meetings</CardTitle><CardDescription>{metrics.pending}</CardDescription></Card>
        <Card><CardTitle>Missed Meetings</CardTitle><CardDescription>{metrics.missed}</CardDescription></Card>
        <Card><CardTitle>AI Summaries Generated</CardTitle><CardDescription>{metrics.summarized}</CardDescription></Card>
      </div>

      <Card className="space-y-4">
        <CardTitle>Filters</CardTitle>
        <CardDescription>Filter by employee, manager, date range, and lifecycle status.</CardDescription>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={employeeFilter} onChange={(event) => setEmployeeFilter(event.target.value)}>
            <option value="all">All Employees</option>
            {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}
          </select>
          <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={managerFilter} onChange={(event) => setManagerFilter(event.target.value)}>
            <option value="all">All Managers</option>
            {managers.map((manager) => <option key={manager.id} value={manager.id}>{manager.name}</option>)}
          </select>
          <Input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
          <Input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
          <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}>
            <option value="all">All Statuses</option>
            <option value="normal">Normal</option>
            <option value="completed">Completed</option>
            <option value="missed">Missed</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle>Meetings</CardTitle>
            <CardDescription>Switch between list and monthly calendar view.</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant={view === "list" ? "default" : "outline"} onClick={() => setView("list")}><List className="mr-2 h-4 w-4" /> List View</Button>
            <Button variant={view === "calendar" ? "default" : "outline"} onClick={() => setView("calendar")}><CalendarDays className="mr-2 h-4 w-4" /> Calendar View</Button>
          </div>
        </div>

        {view === "list" ? (
          <div className="space-y-3">
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading meetings...</p>
            ) : filteredMeetings.length === 0 ? (
              <p className="rounded-lg border border-dashed border-border p-5 text-sm text-muted-foreground">No meetings yet. Schedule one to get started.</p>
            ) : (
              filteredMeetings.map((meeting) => {
                const state = lifecycleStatus(meeting);
                return (
                  <div key={meeting.id} className="rounded-xl border border-border/70 bg-background/40 p-4 transition hover:border-primary/35 hover:shadow-card">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-1">
                        <p className="font-semibold text-foreground">{meeting.title || `${meeting.employee_name || "Employee"} sync`}</p>
                        <p className="text-xs text-muted-foreground">{meeting.employee_name || "Employee"} with {meeting.manager_name || "Manager"}</p>
                        <p className="text-xs text-muted-foreground">{new Date(meeting.start_time).toLocaleString()} · {meeting.duration_minutes} min · {meeting.created_by_role || "manager"}</p>
                      </div>
                      <Badge className={statusBadgeClass(state)}>{statusText(state)}</Badge>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      <p>Description: {meeting.description || "No description"}</p>
                      <p>Participants: {(meeting.participants || []).join(", ") || "None"}</p>
                      <p>Meeting Link: {meeting.meet_link || "Generated on create"}</p>
                      <p>Summary: {meeting.summary || "Not generated"}</p>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <Button size="sm" variant="outline" onClick={() => setDetailOpenFor(meeting)}>View</Button>
                      <Button size="sm" variant="outline" onClick={() => meeting.meet_link && window.open(meeting.meet_link, "_blank", "noopener,noreferrer")} disabled={!meeting.meet_link}>
                        <ExternalLink className="mr-1 h-3.5 w-3.5" /> Join
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const start = new Date(meeting.start_time);
                          const end = new Date(meeting.end_time);
                          setScheduleForm((prev) => ({
                            ...prev,
                            title: meeting.title || "",
                            description: meeting.description || "",
                            start_time: `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, "0")}-${String(start.getDate()).padStart(2, "0")}T${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")}`,
                            end_time: `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}T${String(end.getHours()).padStart(2, "0")}:${String(end.getMinutes()).padStart(2, "0")}`,
                            additional_participants: (meeting.participants || []).join(", "),
                          }));
                          setRescheduleOpenFor(meeting);
                        }}
                      >
                        Reschedule
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => cancelMeeting(meeting.id).catch(() => null)} disabled={saving}>Cancel</Button>
                      <Button size="sm" variant="outline" onClick={() => setSummaryOpenFor(meeting.id)}>View Summary</Button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Button variant="outline" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1))}>Previous</Button>
              <p className="font-medium text-foreground">{calendarMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" })}</p>
              <Button variant="outline" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1))}>Next</Button>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-7">
              {monthDays.map((date) => {
                const key = date.toISOString().slice(0, 10);
                const dayMeetings = meetingsByDate.get(key) || [];
                return (
                  <div key={key} className="rounded-xl border border-border/70 bg-background/50 p-3">
                    <p className="text-xs text-muted-foreground">{dayLabel(date)}</p>
                    <p className="text-sm font-semibold text-foreground">{date.getDate()}</p>
                    <div className="mt-2 space-y-1">
                      {dayMeetings.slice(0, 3).map((meeting) => {
                        const state = lifecycleStatus(meeting);
                        return (
                          <button
                            key={meeting.id}
                            className={`w-full rounded-md px-2 py-1 text-left text-[11px] ${statusBadgeClass(state)}`}
                            onClick={() => setDetailOpenFor(meeting)}
                          >
                            {meeting.employee_name || "Employee"}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-primary" /> Blue: Normal</span>
              <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-success" /> Green: Completed</span>
              <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-error" /> Red: Missed</span>
              <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-warning" /> Yellow: Pending</span>
            </div>
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <CardTitle>Meeting Lifecycle</CardTitle>
        <CardDescription>Check-in submitted → auto-created → manager approves → scheduled → meeting done → AI summary → rating submitted.</CardDescription>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-border/70 p-3 text-sm">1. Check-in Submitted</div>
          <div className="rounded-lg border border-border/70 p-3 text-sm">2. Proposal / Scheduling</div>
          <div className="rounded-lg border border-border/70 p-3 text-sm">3. Meeting + Summary</div>
          <div className="rounded-lg border border-border/70 p-3 text-sm">4. Rating + Closure</div>
        </div>
      </Card>

      {scheduleOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-2xl space-y-4">
            <div className="flex items-center justify-between">
              <CardTitle>Schedule Meeting</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setScheduleOpen(false)}><XCircle className="h-5 w-5" /></Button>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Input placeholder="Meeting title" value={scheduleForm.title} onChange={(event) => setScheduleForm((prev) => ({ ...prev, title: event.target.value }))} />
              <Input type="datetime-local" value={scheduleForm.start_time} onChange={(event) => setScheduleForm((prev) => ({ ...prev, start_time: event.target.value }))} />
              <Input type="datetime-local" value={scheduleForm.end_time} onChange={(event) => setScheduleForm((prev) => ({ ...prev, end_time: event.target.value }))} />
              <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={teamManagerId} onChange={(event) => setTeamManagerId(event.target.value)}>
                <option value="">Select Team Manager (optional)</option>
                {managers.map((manager) => <option key={manager.id} value={manager.id}>{manager.name}</option>)}
              </select>
            </div>
            <Textarea value={scheduleForm.description} onChange={(event) => setScheduleForm((prev) => ({ ...prev, description: event.target.value }))} placeholder="Description" />

            <div className="space-y-2 rounded-lg border border-border/70 bg-background/50 p-3">
              <p className="text-sm font-medium text-foreground">Participant Groups</p>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3 text-sm">
                <label className="inline-flex items-center gap-2">
                  <input type="checkbox" checked={includeAllEmployees} onChange={(event) => setIncludeAllEmployees(event.target.checked)} />
                  Select All Employees
                </label>
                <label className="inline-flex items-center gap-2">
                  <input type="checkbox" checked={includeAllManagers} onChange={(event) => setIncludeAllManagers(event.target.checked)} />
                  Select All Managers
                </label>
                <label className="inline-flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeTeamMembers}
                    onChange={(event) => setIncludeTeamMembers(event.target.checked)}
                    disabled={!teamManagerId}
                  />
                  Select Team Members
                </label>
              </div>
              {includeTeamMembers && !teamManagerId ? <p className="text-xs text-warning">Choose a manager to enable team selection.</p> : null}
            </div>

            <div className="space-y-2 rounded-lg border border-border/70 bg-background/50 p-3">
              <p className="text-sm font-medium text-foreground">Individual Selection</p>
              <div className="max-h-44 overflow-y-auto rounded-md border border-border/60 p-2">
                <div className="grid grid-cols-1 gap-1 text-sm md:grid-cols-2">
                  {selectableParticipants.map((participant) => (
                    <label key={participant.email} className="inline-flex items-center gap-2 rounded-md px-2 py-1 hover:bg-muted/40">
                      <input
                        type="checkbox"
                        checked={selectedParticipantEmails.includes(participant.email)}
                        onChange={() => toggleIndividualParticipant(participant.email)}
                      />
                      <span>{participant.label} <span className="text-xs text-muted-foreground">({participant.kind})</span></span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <Input
              placeholder="Additional participant emails (comma-separated)"
              value={scheduleForm.additional_participants}
              onChange={(event) => setScheduleForm((prev) => ({ ...prev, additional_participants: event.target.value }))}
            />
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">{participantCountLabel}</p>
              <div className="flex flex-wrap gap-2">
                {participantChips.length === 0 ? <span className="text-xs text-muted-foreground">No participants selected</span> : null}
                {participantChips.map((chip) => (
                  <Badge key={chip} className="border-border bg-transparent text-foreground ring-0">{chip}</Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Invites will be sent to: {participantPreview.join(", ") || "No participants"}</p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setScheduleOpen(false)}>Close</Button>
              <Button onClick={() => scheduleMeeting().catch(() => null)} disabled={saving}>Create Meeting</Button>
            </div>
          </Card>
        </div>
      )}

      {rescheduleOpenFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-xl space-y-4">
            <CardTitle>Reschedule Meeting</CardTitle>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Input placeholder="Meeting title" value={scheduleForm.title} onChange={(event) => setScheduleForm((prev) => ({ ...prev, title: event.target.value }))} />
              <Input type="datetime-local" value={scheduleForm.start_time} onChange={(event) => setScheduleForm((prev) => ({ ...prev, start_time: event.target.value }))} />
              <Input type="datetime-local" value={scheduleForm.end_time} onChange={(event) => setScheduleForm((prev) => ({ ...prev, end_time: event.target.value }))} />
              <Input
                placeholder="Additional participant emails (comma-separated)"
                value={scheduleForm.additional_participants}
                onChange={(event) => setScheduleForm((prev) => ({ ...prev, additional_participants: event.target.value }))}
              />
            </div>
            <Textarea value={scheduleForm.description} onChange={(event) => setScheduleForm((prev) => ({ ...prev, description: event.target.value }))} placeholder="Description" />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setRescheduleOpenFor(null)}>Close</Button>
              <Button onClick={() => rescheduleMeeting().catch(() => null)} disabled={saving}>Update</Button>
            </div>
          </Card>
        </div>
      )}

      {summaryOpenFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-xl space-y-4">
            <CardTitle>AI Meeting Summary</CardTitle>
            <CardDescription>Paste transcript to generate key discussion summary.</CardDescription>
            <Textarea value={transcriptByMeeting[summaryOpenFor] || ""} onChange={(event) => setTranscriptByMeeting((prev) => ({ ...prev, [summaryOpenFor]: event.target.value }))} placeholder="Paste transcript" />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSummaryOpenFor(null)}>Close</Button>
              <Button onClick={() => summarizeMeeting(summaryOpenFor).catch(() => null)} disabled={saving}>Generate Summary</Button>
            </div>
          </Card>
        </div>
      )}

      {detailOpenFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-2xl space-y-4">
            <div className="flex items-center justify-between">
              <CardTitle>Meeting Details</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setDetailOpenFor(null)}><XCircle className="h-5 w-5" /></Button>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 text-sm">
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Title</p><p>{detailOpenFor.title || "Untitled"}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Created By</p><p>{detailOpenFor.created_by_role || "manager"}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Employee</p><p>{detailOpenFor.employee_name || "Unknown"}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Manager</p><p>{detailOpenFor.manager_name || "Unknown"}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Time</p><p>{new Date(detailOpenFor.start_time).toLocaleString()}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Duration</p><p>{detailOpenFor.duration_minutes} minutes</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Lifecycle</p><p>{statusText(lifecycleStatus(detailOpenFor))}</p></div>
              <div className="rounded-lg border border-border/70 p-3"><p className="font-medium">Rating</p><p>{detailOpenFor.rating_given ? "Submitted" : "Pending"}</p></div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-border/70 p-3 text-sm">
                <p className="font-medium inline-flex items-center gap-1"><Clock3 className="h-4 w-4" /> Progress</p>
                <p className="text-muted-foreground">{detailOpenFor.created_from_checkin ? "Created from check-in" : "Manual schedule"}</p>
              </div>
              <div className="rounded-lg border border-border/70 p-3 text-sm">
                <p className="font-medium inline-flex items-center gap-1"><CircleCheckBig className="h-4 w-4" /> Feedback</p>
                <p className="text-muted-foreground">{detailOpenFor.summary ? "Summary available" : "Summary pending"}</p>
              </div>
              <div className="rounded-lg border border-border/70 p-3 text-sm">
                <p className="font-medium inline-flex items-center gap-1"><TriangleAlert className="h-4 w-4" /> Action Items</p>
                <p className="text-muted-foreground">Audit summary and close follow-ups.</p>
              </div>
            </div>
          </Card>
        </div>
      )}
    </motion.div>
  );
}

