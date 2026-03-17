"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CalendarCheck } from "lucide-react";
import { checkinsService } from "@/services/checkins";
import type { Checkin } from "@/types";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/ui/page-header";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { formatDateTime } from "@/lib/utils";
import { useSessionStore } from "@/store/useSessionStore";
import { aiService } from "@/services/ai";
import { toast } from "sonner";

export default function CheckinsPage() {
  const [items, setItems] = useState<Checkin[]>([]);
  const [goalId, setGoalId] = useState("");
  const [meetingDate, setMeetingDate] = useState("");
  const [notes, setNotes] = useState("");
  const [aiSummary, setAiSummary] = useState("");
  const user = useSessionStore((s) => s.user);

  const load = async () => {
    const data = await checkinsService.getCheckins();
    setItems(data);
  };

  useEffect(() => {
    load().catch(() => null);
  }, []);

  const schedule = async () => {
    if (!user) {
      toast.error("Please sign in again to schedule a check-in");
      return;
    }

    if (!goalId.trim()) {
      toast.error("Goal ID is required");
      return;
    }

    if (!meetingDate) {
      toast.error("Meeting date is required");
      return;
    }

    const meetingIso = new Date(meetingDate);
    if (Number.isNaN(meetingIso.getTime())) {
      toast.error("Please provide a valid meeting date and time");
      return;
    }

    await checkinsService.schedule({
      goal_id: goalId.trim(),
      employee_id: user.id,
      manager_id: user.manager_id || user.id,
      meeting_date: meetingIso.toISOString(),
    });
    setGoalId("");
    setMeetingDate("");
    toast.success("Check-in scheduled");
    await load();
  };

  const summarize = async () => {
    if (!notes.trim()) {
      toast.error("Add meeting notes before generating an AI summary");
      return;
    }
    try {
      const output = await aiService.summarizeCheckin(notes);
      setAiSummary(`${output.summary}\n\nKey Points: ${output.key_points.join(", ")}\nAction Items: ${output.action_items.join(", ")}`);
    } catch (error: unknown) {
      const status =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { status?: number } }).response?.status
          : undefined;

      if (status === 429) {
        toast.error("AI usage limit reached for this quarter. Please try again next cycle.");
        setAiSummary("AI summary is currently unavailable because the quarterly usage limit has been reached.");
        return;
      }

      toast.error("Failed to generate AI summary. Please try again.");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Check-ins"
        description="Schedule one-on-ones, capture notes, and generate AI summaries."
        action={<Button variant="outline" onClick={() => load().catch(() => null)}>Refresh</Button>}
      />

      <SectionContainer columns="dashboard">
        <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 xl:col-span-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <CalendarCheck className="h-3.5 w-3.5" /> Check-in Planner
          </div>
          <CardTitle>Schedule Check-in</CardTitle>
          <CardDescription>Plan one-on-one reviews and track meeting outcomes.</CardDescription>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-1">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Goal ID</label>
              <Input placeholder="Goal ID" value={goalId} onChange={(e) => setGoalId(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Meeting Date</label>
              <Input type="datetime-local" value={meetingDate} onChange={(e) => setMeetingDate(e.target.value)} />
            </div>
          </div>
          <Button onClick={schedule}>Schedule</Button>
        </Card>

        <div className="space-y-6 xl:col-span-8">
          <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Attach Notes + AI Summary</CardTitle>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Meeting Notes</label>
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Add meeting notes..." />
            </div>
            <Button variant="outline" onClick={summarize}>Generate AI Summary</Button>
            {aiSummary && <CardDescription className="whitespace-pre-wrap">{aiSummary}</CardDescription>}
          </Card>

          <Card className="rounded-2xl border border-border/75 bg-card/95">
            <CardTitle>Past Check-ins</CardTitle>
            <div className="mt-4">
              <DataTable
                rows={items}
                rowKey={(row) => row.id}
                emptyState="No check-ins scheduled yet"
                columns={[
                  {
                    key: "status",
                    header: "Status",
                    render: (row) => (
                      <Badge className={row.status === "completed" ? "bg-success/15 text-success" : "bg-warning/15 text-warning"}>
                        {row.status}
                      </Badge>
                    ),
                  },
                  {
                    key: "meeting_date",
                    header: "Meeting Date",
                    render: (row) => formatDateTime(row.meeting_date),
                  },
                  {
                    key: "summary",
                    header: "Summary",
                    render: (row) => row.summary || "-",
                  },
                ]}
              />
            </div>
          </Card>
        </div>
      </SectionContainer>
    </motion.div>
  );
}
