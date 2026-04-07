"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { managerService } from "@/services/manager";
import { meetingsService } from "@/services/meetings";
import { checkinsService } from "@/services/checkins";
import { aiService } from "@/services/ai";
import { useSessionStore } from "@/store/useSessionStore";
import type {
  AIFeedbackCoachingResult,
  CheckinRatingRecommendation,
  CheckinTranscriptIngestResult,
  Meeting,
  MeetingProposal,
} from "@/types";

type RatingDraft = { rating: number; feedback: string };

export default function ManagerApprovalsPage() {
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);
  const [proposals, setProposals] = useState<MeetingProposal[]>([]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [rejectSuggestionByProposal, setRejectSuggestionByProposal] = useState<Record<string, string>>({});
  const [ratingsByCheckin, setRatingsByCheckin] = useState<Record<string, RatingDraft>>({});
  const [transcriptByCheckin, setTranscriptByCheckin] = useState<Record<string, string>>({});
  const [transcriptInsightsByCheckin, setTranscriptInsightsByCheckin] = useState<Record<string, CheckinTranscriptIngestResult>>({});
  const [recommendationByCheckin, setRecommendationByCheckin] = useState<Record<string, CheckinRatingRecommendation>>({});
  const [coachingByCheckin, setCoachingByCheckin] = useState<Record<string, AIFeedbackCoachingResult>>({});

  const load = async () => {
    const [pendingProposals, allMeetings] = await Promise.all([
      managerService.getPendingMeetingProposals(),
      meetingsService.getMeetings(),
    ]);
    setProposals(pendingProposals);
    setMeetings(allMeetings);
  };

  useEffect(() => {
    if (!user) {
      return;
    }
    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, setActiveMode, user]);

  useEffect(() => {
    if (!user || activeMode !== "manager") {
      return;
    }
    load().catch(() => {
      toast.error("Failed to load approvals data");
    });
  }, [activeMode, user]);

  const ratableMeetings = useMemo(() => {
    const now = Date.now();
    return meetings.filter((meeting) => {
      if (!meeting.checkin_id) return false;
      if (meeting.status === "cancelled") return false;
      const endTime = new Date(meeting.end_time).getTime();
      return !Number.isNaN(endTime) && endTime <= now;
    });
  }, [meetings]);

  const approve = async (proposalId: string) => {
    try {
      await managerService.approveMeetingProposal(proposalId);
      setProposals((prev) => prev.filter((item) => item.id !== proposalId));
      toast.success("Meeting proposal approved and scheduled");
      await load();
    } catch {
      toast.error("Failed to approve meeting proposal");
    }
  };

  const reject = async (proposalId: string) => {
    try {
      const suggest = rejectSuggestionByProposal[proposalId]?.trim();
      await managerService.rejectMeetingProposal(proposalId, suggest ? new Date(suggest).toISOString() : undefined);
      setProposals((prev) => prev.filter((item) => item.id !== proposalId));
      setRejectSuggestionByProposal((prev) => ({ ...prev, [proposalId]: "" }));
      toast.success("Meeting proposal rejected");
    } catch {
      toast.error("Failed to reject meeting proposal");
    }
  };

  const submitRating = async (checkinId: string) => {
    const draft = ratingsByCheckin[checkinId] ?? { rating: 4, feedback: "" };
    if (draft.rating < 1 || draft.rating > 5) {
      toast.error("Rating must be between 1 and 5");
      return;
    }

    try {
      await checkinsService.rate(checkinId, {
        rating: draft.rating,
        feedback: draft.feedback.trim() || undefined,
      });
      toast.success("Check-in rated successfully");
      setRatingsByCheckin((prev) => ({ ...prev, [checkinId]: { rating: 4, feedback: "" } }));
      await load();
    } catch {
      toast.error("Failed to submit rating");
    }
  };

  const ingestTranscript = async (checkinId: string) => {
    const transcript = (transcriptByCheckin[checkinId] || "").trim();
    if (transcript.length < 10) {
      toast.error("Transcript must be at least 10 characters");
      return;
    }

    try {
      const output = await checkinsService.ingestTranscript(checkinId, transcript);
      setTranscriptInsightsByCheckin((prev) => ({ ...prev, [checkinId]: output }));
      toast.success("Transcript ingested and goal summaries updated");
    } catch {
      toast.error("Failed to ingest transcript");
    }
  };

  const loadRatingRecommendation = async (checkinId: string) => {
    try {
      const recommendation = await checkinsService.getRatingRecommendation(checkinId);
      setRecommendationByCheckin((prev) => ({ ...prev, [checkinId]: recommendation }));
      setRatingsByCheckin((prev) => ({
        ...prev,
        [checkinId]: {
          ...(prev[checkinId] ?? { rating: 4, feedback: "" }),
          rating: recommendation.suggested_rating,
        },
      }));
      toast.success("Rating recommendation applied. You can still override it.");
    } catch {
      toast.error("Failed to load rating recommendation");
    }
  };

  const coachFeedback = async (checkinId: string) => {
    const draft = ratingsByCheckin[checkinId] ?? { rating: 4, feedback: "" };
    const input = draft.feedback.trim();
    if (!input) {
      toast.error("Enter feedback text first");
      return;
    }

    try {
      const coaching = await aiService.coachFeedback(input);
      setCoachingByCheckin((prev) => ({ ...prev, [checkinId]: coaching }));
      setRatingsByCheckin((prev) => ({
        ...prev,
        [checkinId]: {
          ...(prev[checkinId] ?? { rating: 4, feedback: "" }),
          feedback: coaching.suggested_version,
        },
      }));
      toast.success(`Feedback coached (tone score ${coaching.tone_score}/10)`);
    } catch {
      toast.error("Failed to coach feedback");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pending Meeting Approvals"
        description="Approve or reject proposed check-in meetings, then rate employees after meetings end."
        action={<Button variant="outline" onClick={() => load().catch(() => toast.error("Refresh failed"))}>Refresh</Button>}
      />

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Meeting Proposals</CardTitle>
        <CardDescription>System-generated proposals from submitted employee check-ins.</CardDescription>
        {proposals.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending meeting proposals.</p>
        ) : (
          proposals.map((proposal) => (
            <div key={proposal.id} className="space-y-2 rounded-md border border-border/70 p-3">
              <p className="text-sm font-medium">Check-in: {proposal.checkin_id}</p>
              <p className="text-xs text-muted-foreground">
                Proposed: {new Date(proposal.proposed_start_time).toLocaleString()} - {new Date(proposal.proposed_end_time).toLocaleString()}
              </p>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Optional alternate start time before reject</label>
                <Input
                  type="datetime-local"
                  value={rejectSuggestionByProposal[proposal.id] || ""}
                  onChange={(event) => setRejectSuggestionByProposal((prev) => ({ ...prev, [proposal.id]: event.target.value }))}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" onClick={() => approve(proposal.id)}>Approve</Button>
                <Button size="sm" variant="outline" onClick={() => reject(proposal.id)}>Reject</Button>
              </div>
            </div>
          ))
        )}
      </Card>

      <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Post-Meeting Ratings</CardTitle>
        <CardDescription>Ratings are enabled after a scheduled check-in meeting has ended.</CardDescription>
        {ratableMeetings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No meetings are ready for rating yet.</p>
        ) : (
          ratableMeetings.map((meeting) => {
            const checkinId = meeting.checkin_id as string;
            const ratingDraft = ratingsByCheckin[checkinId] ?? { rating: 4, feedback: "" };
            return (
              <div key={meeting.id} className="space-y-2 rounded-md border border-border/70 p-3">
                <p className="text-sm font-medium">Meeting: {meeting.title}</p>
                <p className="text-xs text-muted-foreground">Check-in: {checkinId}</p>
                <p className="text-xs text-muted-foreground">Ended: {new Date(meeting.end_time).toLocaleString()}</p>

                <div className="space-y-2 rounded-md border border-border/70 p-3">
                  <label className="text-xs text-muted-foreground">Transcript (manual paste or synced notes)</label>
                  <Textarea
                    value={transcriptByCheckin[checkinId] || ""}
                    onChange={(event) => {
                      const value = event.target.value;
                      setTranscriptByCheckin((prev) => ({ ...prev, [checkinId]: value }));
                    }}
                    placeholder="Paste transcript to auto-generate check-in summary and goal-level notes"
                  />
                  <Button size="sm" variant="outline" onClick={() => ingestTranscript(checkinId)}>
                    Ingest Transcript and Map to Goals
                  </Button>
                  {transcriptInsightsByCheckin[checkinId] ? (
                    <div className="space-y-1 text-xs text-muted-foreground">
                      <p className="font-medium text-foreground">AI Summary</p>
                      <p>{transcriptInsightsByCheckin[checkinId].summary}</p>
                    </div>
                  ) : null}
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Rating (1-5)</label>
                  <Input
                    type="number"
                    min={1}
                    max={5}
                    value={ratingDraft.rating}
                    onChange={(event) => {
                      const value = Number(event.target.value || 0);
                      setRatingsByCheckin((prev) => ({ ...prev, [checkinId]: { ...ratingDraft, rating: value } }));
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Feedback</label>
                  <Textarea
                    value={ratingDraft.feedback}
                    onChange={(event) => {
                      const value = event.target.value;
                      setRatingsByCheckin((prev) => ({ ...prev, [checkinId]: { ...ratingDraft, feedback: value } }));
                    }}
                    placeholder="Add qualitative feedback"
                  />
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" onClick={() => loadRatingRecommendation(checkinId)}>
                    Get AI Rating Recommendation
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => coachFeedback(checkinId)}>
                    Coach Feedback Tone
                  </Button>
                  <Button size="sm" onClick={() => submitRating(checkinId)}>Submit Rating</Button>
                </div>

                {recommendationByCheckin[checkinId] ? (
                  <div className="space-y-1 rounded-md border border-border/70 p-3 text-xs text-muted-foreground">
                    <p className="font-medium text-foreground">
                      Suggested Rating: {recommendationByCheckin[checkinId].suggested_rating}/5
                      {" "}(confidence {Math.round(recommendationByCheckin[checkinId].confidence * 100)}%)
                    </p>
                    {recommendationByCheckin[checkinId].rationale.map((line, idx) => (
                      <p key={`${checkinId}-rationale-${idx}`}>{line}</p>
                    ))}
                  </div>
                ) : null}

                {coachingByCheckin[checkinId] ? (
                  <p className="text-xs text-muted-foreground">
                    Coaching applied. Tone score: {coachingByCheckin[checkinId].tone_score}/10
                  </p>
                ) : null}
              </div>
            );
          })
        )}
      </Card>
    </div>
  );
}
