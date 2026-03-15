"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CalendarDays } from "lucide-react";
import { useMeetingsStore } from "@/store/useMeetingsStore";
import { useSessionStore } from "@/store/useSessionStore";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { MeetingCard } from "@/components/meetings/MeetingCard";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { authService } from "@/services/auth";

const defaultGoogleAccessToken = process.env.NEXT_PUBLIC_GOOGLE_ACCESS_TOKEN || "";

export default function MeetingsPage() {
  const { meetings, loading, fetchMeetings, createMeeting } = useMeetingsStore();
  const { googleAccessToken, setGoogleAccessToken } = useSessionStore();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [goalId, setGoalId] = useState("");
  const [participants, setParticipants] = useState("");
  const [manualAccessToken, setManualAccessToken] = useState(googleAccessToken ?? defaultGoogleAccessToken);

  const validateGoogleToken = (token: string) => {
    const trimmed = token.trim();
    if (!trimmed) return false;
    if (trimmed.startsWith("AIza")) {
      toast.error("Google API key detected. Use a Google OAuth access token for Meet (usually starts with ya29.)");
      return false;
    }
    return true;
  };

  useEffect(() => {
    if (!googleAccessToken && defaultGoogleAccessToken && validateGoogleToken(defaultGoogleAccessToken)) {
      setGoogleAccessToken(defaultGoogleAccessToken.trim());
    }
  }, [googleAccessToken, setGoogleAccessToken]);

  useEffect(() => {
    if (googleAccessToken) {
      fetchMeetings(googleAccessToken).catch(() => null);
    }
  }, [fetchMeetings, googleAccessToken]);

  const submit = async () => {
    if (!googleAccessToken) {
      toast.error("Google OAuth access token is required to create meetings");
      return;
    }

    if (!title.trim()) {
      toast.error("Meeting title is required");
      return;
    }

    if (!start || !end) {
      toast.error("Start and end times are required");
      return;
    }

    const startDate = new Date(start);
    const endDate = new Date(end);

    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      toast.error("Please provide valid start and end times");
      return;
    }

    if (endDate <= startDate) {
      toast.error("End time must be after start time");
      return;
    }

    if (!goalId.trim()) {
      toast.error("Goal ID is required");
      return;
    }

    const participantList = participants.split(",").map((p) => p.trim()).filter(Boolean);

    if (participantList.length === 0) {
      toast.error("At least one participant email is required");
      return;
    }

    await createMeeting(
      {
        title: title.trim(),
        description,
        start_time: startDate.toISOString(),
        end_time: endDate.toISOString(),
        goal_id: goalId.trim(),
        participants: participantList,
      },
      googleAccessToken,
    );
    setTitle("");
    setDescription("");
    setStart("");
    setEnd("");
    setGoalId("");
    setParticipants("");
    toast.success("Meeting created");
  };

  const connectGoogleCalendar = async () => {
    try {
      const { authorization_url } = await authService.getGoogleAuthorizeUrl();
      if (!authorization_url) {
        toast.error("Google OAuth is not configured on backend");
        return;
      }
      window.location.href = authorization_url;
    } catch {
      toast.error("Failed to initialize Google OAuth flow");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <PageHeader
        title="Meetings"
        description="Create and track Google Calendar meetings with Meet links and participants."
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={connectGoogleCalendar}>Connect Google Calendar</Button>
            <Button
              variant="outline"
              onClick={() => {
                if (googleAccessToken) {
                  fetchMeetings(googleAccessToken).catch(() => null);
                  return;
                }

                toast.error("Connect Google Calendar or add an access token before refreshing meetings");
              }}
            >
              Refresh
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <Card className="space-y-4 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <CalendarDays className="h-3.5 w-3.5" /> Meeting Scheduler
          </div>
          <CardTitle>Schedule Meeting</CardTitle>
          <CardDescription>Create Google Calendar event with Meet link and invites.</CardDescription>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Google Access Token</label>
            <Input
              placeholder="Google access token"
              value={manualAccessToken}
              onChange={(e) => setManualAccessToken(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Meet endpoints require a Google OAuth access token (not an API key).
            </p>
          </div>
          <Button
            onClick={() => {
              if (!validateGoogleToken(manualAccessToken)) return;
              setGoogleAccessToken(manualAccessToken.trim());
            }}
            disabled={!manualAccessToken.trim()}
            variant="outline"
          >
            Use Access Token
          </Button>

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
              <label className="text-sm font-medium text-foreground">Goal ID</label>
              <Input placeholder="Goal ID" value={goalId} onChange={(e) => setGoalId(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Participants</label>
              <Input placeholder="email1@company.com, email2@company.com" value={participants} onChange={(e) => setParticipants(e.target.value)} />
            </div>
          </div>

          <Button onClick={submit} disabled={!googleAccessToken}>Create Meeting</Button>
        </Card>

        <div className="space-y-6 xl:col-span-8">
          <Card>
            <CardTitle>Meeting Timeline</CardTitle>
            <CardDescription>Upcoming and historical meetings synced with Google Calendar.</CardDescription>
          </Card>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {loading
              ? Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-44" />)
              : meetings.map((meeting) => <MeetingCard key={meeting.id} meeting={meeting} />)}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
