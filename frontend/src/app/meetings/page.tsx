"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { CalendarDays } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMeetingsStore } from "@/store/useMeetingsStore";
import { checkinsService } from "@/services/checkins";
import { meetingsService } from "@/services/meetings";
import { useEmployeeDashboard } from "@/hooks/useDashboardData";
import type { Checkin, Goal } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { MeetingCard } from "@/components/meetings/MeetingCard";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { authService } from "@/services/auth";
import { goalsService } from "@/services/goals";

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === "object") {
    const maybeAxios = error as {
      response?: { data?: { error?: unknown; message?: unknown } };
      message?: unknown;
    };
    const apiError = maybeAxios.response?.data?.error;
    if (typeof apiError === "string" && apiError.trim()) {
      return apiError;
    }
    const apiMessage = maybeAxios.response?.data?.message;
    if (typeof apiMessage === "string" && apiMessage.trim()) {
      return apiMessage;
    }
    if (typeof maybeAxios.message === "string" && maybeAxios.message.trim()) {
      return maybeAxios.message;
    }
  }
  return "Request failed";
}

const MEETING_DRAFT_KEY = "pms-meeting-draft";

interface MeetingDraft {
  title: string;
  description: string;
  start: string;
  end: string;
  checkinIds: string[];
  selectedGoalIds: string[];
  meetingType: "CHECKIN" | "GENERAL" | "REVIEW";
  participants: string;
}

export default function MeetingsPage() {
  const router = useRouter();
  const { meetings, loading, fetchMeetings, createMeeting } = useMeetingsStore();
  const { data: dashboardData } = useEmployeeDashboard();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [meetingType, setMeetingType] = useState<"CHECKIN" | "GENERAL" | "REVIEW">("GENERAL");
  const [checkinIds, setCheckinIds] = useState<string[]>([]);
  const [selectedGoalIds, setSelectedGoalIds] = useState<string[]>([]);
  const [participants, setParticipants] = useState("");
  const [checkins, setCheckins] = useState<Checkin[]>([]);
  const [goalsById, setGoalsById] = useState<Record<string, Goal>>({});
  const [checkinsLoading, setCheckinsLoading] = useState(false);
  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null);
  const oauthHandledRef = useRef(false);

  const getCurrentDraft = useCallback((): MeetingDraft => ({
    title,
    description,
    start,
    end,
    checkinIds,
    selectedGoalIds,
    meetingType,
    participants,
  }), [checkinIds, description, end, meetingType, participants, selectedGoalIds, start, title]);

  const persistDraft = useCallback(() => {
    if (typeof window === "undefined") return;
    sessionStorage.setItem(MEETING_DRAFT_KEY, JSON.stringify(getCurrentDraft()));
  }, [getCurrentDraft]);

  const clearDraft = () => {
    if (typeof window === "undefined") return;
    sessionStorage.removeItem(MEETING_DRAFT_KEY);
  };

  const restoreDraft = (): MeetingDraft | null => {
    if (typeof window === "undefined") return null;
    const raw = sessionStorage.getItem(MEETING_DRAFT_KEY);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw) as (Partial<MeetingDraft> & { checkinId?: string });
      const normalizedMeetingType = (parsed.meetingType as "CHECKIN" | "GENERAL" | "REVIEW") ?? "GENERAL";
      const parsedCheckinIds =
        Array.isArray(parsed.checkinIds)
          ? parsed.checkinIds.filter((id): id is string => typeof id === "string" && id.trim().length > 0)
          : typeof parsed.checkinId === "string" && parsed.checkinId.trim().length > 0
            ? [parsed.checkinId.trim()]
            : [];
      return {
        title: parsed.title ?? "",
        description: parsed.description ?? "",
        start: parsed.start ?? "",
        end: parsed.end ?? "",
        meetingType: normalizedMeetingType,
        checkinIds: normalizedMeetingType === "CHECKIN" ? parsedCheckinIds : [],
        selectedGoalIds:
          normalizedMeetingType === "CHECKIN"
            ? Array.isArray(parsed.selectedGoalIds)
              ? parsed.selectedGoalIds
              : []
            : [],
        participants: parsed.participants ?? "",
      };
    } catch {
      return null;
    }
  };

  const applyDraft = (draft: MeetingDraft) => {
    setTitle(draft.title);
    setDescription(draft.description);
    setStart(draft.start);
    setEnd(draft.end);
    setMeetingType(draft.meetingType);
    setCheckinIds(draft.checkinIds || []);
    setSelectedGoalIds(draft.selectedGoalIds || []);
    setParticipants(draft.participants);
  };

  useEffect(() => {
    fetchMeetings().catch(() => null);
  }, [fetchMeetings]);

  useEffect(() => {
    setCheckinsLoading(true);
    checkinsService
      .getCheckins()
      .then((items) => {
        setCheckins(items);
      })
      .catch(() => {
        setCheckins([]);
      })
      .finally(() => {
        setCheckinsLoading(false);
      });
  }, []);

  useEffect(() => {
    goalsService
      .getGoals()
      .then((items) => {
        const map: Record<string, Goal> = {};
        for (const goal of items) {
          map[goal.id] = goal;
        }
        setGoalsById(map);
      })
      .catch(() => {
        setGoalsById({});
      });
  }, []);

  useEffect(() => {
    authService
      .getGoogleConnectionStatus()
      .then((status) => setGoogleConnected(status.connected))
      .catch(() => setGoogleConnected(null));
  }, []);

  useEffect(() => {
    if (meetingType !== "CHECKIN") {
      setCheckinIds([]);
      setSelectedGoalIds([]);
    }
  }, [meetingType]);

  useEffect(() => {
    if (meetingType !== "CHECKIN") return;
    if (checkinIds.length === 0) {
      setSelectedGoalIds([]);
      return;
    }

    const availableCheckinIds = new Set(checkins.map((item) => item.id));
    const normalizedIds = checkinIds.filter((id) => availableCheckinIds.has(id));
    if (normalizedIds.length !== checkinIds.length) {
      setCheckinIds(normalizedIds);
      return;
    }

    const unionGoalIds = new Set<string>();
    for (const id of normalizedIds) {
      const linked = checkins.find((item) => item.id === id);
      for (const goalId of linked?.goal_ids ?? []) {
        unionGoalIds.add(goalId);
      }
    }

    if (unionGoalIds.size === 0) {
      setSelectedGoalIds([]);
      return;
    }

    setSelectedGoalIds((prev) => {
      const filtered = prev.filter((id) => unionGoalIds.has(id));
      return filtered.length > 0 ? filtered : Array.from(unionGoalIds);
    });
  }, [checkinIds, checkins, meetingType]);

  useEffect(() => {
    if (meetingType !== "CHECKIN" || !dashboardData?.manager_email) {
      return;
    }

    if (checkinIds.length === 0) {
      setParticipants("");
      return;
    }

    // Auto-populate manager email for check-in meetings
    const managerEmail = dashboardData.manager_email.trim();
     setParticipants((prev) => {
       if (managerEmail && !prev.includes(managerEmail)) {
         return managerEmail;
       }
       return prev;
     });
    }, [meetingType, checkinIds, dashboardData?.manager_email]);

  const selectedCheckins = meetingType === "CHECKIN" ? checkins.filter((item) => checkinIds.includes(item.id)) : [];
  const checkinGoals = Array.from(new Set(selectedCheckins.flatMap((checkin) => checkin.goal_ids || []))).map((goalId) => ({
    id: goalId,
    title: goalsById[goalId]?.title || `Goal ${goalId.slice(0, 8)}`,
  }));

  const connectGoogleCalendar = useCallback(async () => {
    try {
      persistDraft();
      const { authorization_url } = await authService.getGoogleAuthorizeUrl();
      if (!authorization_url) {
        toast.error("Google OAuth is not configured on backend");
        return;
      }
      window.location.href = authorization_url;
    } catch {
      toast.error("Failed to initialize Google OAuth flow");
    }
  }, [persistDraft]);

  const submit = useCallback(async (draftOverride?: MeetingDraft) => {
    const source = draftOverride ?? getCurrentDraft();

    if (!source.title.trim()) {
      toast.error("Meeting title is required");
      return;
    }

    if (!source.start || !source.end) {
      toast.error("Start and end times are required");
      return;
    }

    const startDate = new Date(source.start);
    const endDate = new Date(source.end);

    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      toast.error("Please provide valid start and end times");
      return;
    }

    if (endDate <= startDate) {
      toast.error("End time must be after start time");
      return;
    }

    if (source.meetingType === "CHECKIN" && source.checkinIds.length === 0) {
      toast.error("Select at least one check-in for check-in meetings");
      return;
    }

    if (source.meetingType === "CHECKIN" && source.selectedGoalIds.length === 0) {
      toast.error("Select at least one goal for this check-in meeting");
      return;
    }

    const participantList = source.participants.split(",").map((p) => p.trim()).filter(Boolean);

    if (source.meetingType !== "CHECKIN" && participantList.length === 0) {
      toast.error("At least one participant email is required");
      return;
    }

    try {
      if (source.meetingType === "CHECKIN") {
        const checkinById = new Map(checkins.map((item) => [item.id, item]));

        for (const selectedCheckinId of source.checkinIds) {
          const linkedGoals = checkinById.get(selectedCheckinId)?.goal_ids ?? [];
          const scopedGoalIds = source.selectedGoalIds.filter((goalId) => linkedGoals.includes(goalId));

          await meetingsService.createMeeting({
            title: source.title.trim(),
            meeting_type: source.meetingType,
            description: source.description,
            start_time: startDate.toISOString(),
            end_time: endDate.toISOString(),
            checkin_id: selectedCheckinId,
            goal_ids: scopedGoalIds.length > 0 ? scopedGoalIds : linkedGoals,
            participants: participantList,
          });
        }
        await fetchMeetings();
      } else {
        await createMeeting({
          title: source.title.trim(),
          meeting_type: source.meetingType,
          description: source.description,
          start_time: startDate.toISOString(),
          end_time: endDate.toISOString(),
          participants: participantList,
        });
      }

      setTitle("");
      setDescription("");
      setStart("");
      setEnd("");
      setMeetingType("GENERAL");
      setCheckinIds([]);
      setSelectedGoalIds([]);
      setParticipants("");
      clearDraft();

      if (source.meetingType === "CHECKIN" && source.checkinIds.length > 1) {
        toast.success(`${source.checkinIds.length} check-in meetings created`);
      } else {
        toast.success("Meeting created");
      }
    } catch (error: unknown) {
      const message = extractErrorMessage(error);
      const needsGoogleReconnect =
        message.includes("Google Calendar is not connected") ||
        message.includes("Google access token refresh failed") ||
        message.includes("Google calendar authorization failed") ||
        message.includes("invalid_grant") ||
        message.includes("invalid_client");

      if (needsGoogleReconnect) {
        persistDraft();
        setGoogleConnected(false);
        toast.info("Google session expired or missing. Reconnecting Google Calendar...");
        await connectGoogleCalendar();
        return;
      }
      toast.error(message);
    }
  }, [checkins, connectGoogleCalendar, createMeeting, fetchMeetings, getCurrentDraft, persistDraft]);

  useEffect(() => {
    if (oauthHandledRef.current) {
      return;
    }

    const params = new URLSearchParams(typeof window === "undefined" ? "" : window.location.search);
    const connected = params.get("google_connected");
    const reason = params.get("reason");

    if (!connected && !reason) {
      const draft = restoreDraft();
      if (draft) {
        applyDraft(draft);
      }
      return;
    }

    oauthHandledRef.current = true;

    if (connected === "1") {
      setGoogleConnected(true);
      toast.success("Google Calendar connected successfully");
      const draft = restoreDraft();
      if (draft && draft.title.trim()) {
        applyDraft(draft);
        toast.info("Meeting draft restored. Creating meeting...");
        setTimeout(() => {
          submit(draft).catch(() => null);
        }, 0);
      }
    } else {
      setGoogleConnected(false);
      toast.error(`Google Calendar connection failed${reason ? `: ${reason.replaceAll("_", " ")}` : ""}`);
    }

    router.replace("/meetings");
  }, [router, submit]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Meetings"
        description="Create and track Google Calendar meetings with Meet links and participants."
        action={
          <div className="flex items-center gap-2">
            {googleConnected !== null && (
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${googleConnected ? "bg-success/15 text-success" : "bg-warning/15 text-warning"}`}>
                {googleConnected ? "Google connected" : "Google not connected"}
              </span>
            )}
            <Button variant="outline" onClick={connectGoogleCalendar}>Connect Google Calendar</Button>
            <Button
              variant="outline"
              onClick={() => {
                fetchMeetings().catch(() => null);
              }}
            >
              Refresh
            </Button>
          </div>
        }
      />

      <SectionContainer columns="dashboard">
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <CalendarDays className="h-3.5 w-3.5" /> Meeting Scheduler
          </div>
          <CardTitle>Schedule Meeting</CardTitle>
          <CardDescription>Google Calendar tokens are managed securely by backend using your OAuth refresh token.</CardDescription>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-1">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Title</label>
              <Input placeholder="Goal review sync" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="space-y-2 sm:col-span-2 xl:col-span-1">
              <label className="text-sm font-medium text-foreground">Description</label>
              <Textarea placeholder="Agenda and goals" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Start Time</label>
              <Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">End Time</label>
              <Input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Meeting Type</label>
              <select
                value={meetingType}
                onChange={(e) => setMeetingType(e.target.value as "CHECKIN" | "GENERAL" | "REVIEW")}
                className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground"
              >
                <option value="GENERAL">General</option>
                <option value="CHECKIN">Check-in</option>
                <option value="REVIEW">Review</option>
              </select>
            </div>
            {meetingType === "CHECKIN" && (
              <div className="space-y-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Check-ins</label>
                  {checkinsLoading ? (
                    <p className="text-xs text-muted-foreground">Loading check-ins...</p>
                  ) : checkins.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No check-ins available yet.</p>
                  ) : (
                    <div className="max-h-52 space-y-2 overflow-y-auto rounded-md border border-border/70 p-3">
                      {checkins.map((checkin) => {
                        const checked = checkinIds.includes(checkin.id);
                        const summary = (checkin.summary || "No summary").slice(0, 80);
                        return (
                          <label key={checkin.id} className="flex items-start gap-2 text-sm text-foreground">
                            <input
                              type="checkbox"
                              className="mt-0.5 h-4 w-4 rounded border-border"
                              checked={checked}
                              onChange={(e) => {
                                setCheckinIds((prev) => {
                                  if (e.target.checked) {
                                    return Array.from(new Set([...prev, checkin.id]));
                                  }
                                  return prev.filter((id) => id !== checkin.id);
                                });
                              }}
                            />
                            <span>{new Date(checkin.created_at).toLocaleDateString()} - {summary}</span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Goals for this meeting</label>
                  {checkinIds.length === 0 ? (
                    <p className="text-xs text-muted-foreground">Select one or more check-ins first to choose meeting goals.</p>
                  ) : checkinGoals.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No linked goals found for selected check-ins.</p>
                  ) : (
                    <div className="space-y-2 rounded-md border border-border/70 p-3">
                      {checkinGoals.map((goal) => {
                        const checked = selectedGoalIds.includes(goal.id);
                        return (
                          <label key={goal.id} className="flex items-start gap-2 text-sm text-foreground">
                            <input
                              type="checkbox"
                              className="mt-0.5 h-4 w-4 rounded border-border"
                              checked={checked}
                              onChange={(e) => {
                                setSelectedGoalIds((prev) => {
                                  if (e.target.checked) {
                                    return Array.from(new Set([...prev, goal.id]));
                                  }
                                  return prev.filter((id) => id !== goal.id);
                                });
                              }}
                            />
                            <span>{goal.title}</span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
            {meetingType !== "CHECKIN" ? (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Participants</label>
                <Input placeholder="email1@company.com, email2@company.com" value={participants} onChange={(e) => setParticipants(e.target.value)} />
              </div>
            ) : (
              <div className="space-y-2 rounded-md border border-border/70 bg-muted/30 p-3">
                <p className="text-sm font-medium text-foreground">Participants</p>
                {checkinIds.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Select a check-in above to auto-populate the manager.
                  </p>
                ) : (
                  <div className="space-y-2 text-xs">
                    <p className="text-muted-foreground">
                      Manager will be auto-added:
                    </p>
                    {dashboardData?.manager_name && dashboardData?.manager_email && (
                      <div className="rounded bg-background/50 p-2">
                        <p className="font-medium text-foreground">{dashboardData.manager_name}</p>
                        <p className="text-muted-foreground">{dashboardData.manager_email}</p>
                      </div>
                    )}
                    {!dashboardData?.manager_email && (
                      <p className="text-muted-foreground italic">
                        (No manager assigned)
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <Button onClick={() => submit().catch(() => null)}>Create Meeting</Button>
        </Card>

        <div className="space-y-6 xl:col-span-8">
          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Meeting Timeline</CardTitle>
            <CardDescription>Upcoming and historical meetings synced with Google Calendar.</CardDescription>
          </Card>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {loading
              ? Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-44" />)
              : meetings.map((meeting) => <MeetingCard key={meeting.id} meeting={meeting} />)}
          </div>
        </div>
      </SectionContainer>
    </motion.div>
  );
}

