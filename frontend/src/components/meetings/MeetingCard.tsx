import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";
import { Meeting } from "@/types";
import { meetingsService } from "@/services/meetings";
import { toast } from "sonner";

function statusClass(status: Meeting["status"]) {
  if (status === "completed") return "border-success/25 bg-success/15 text-success";
  if (status === "cancelled") return "border-error/25 bg-error/15 text-error";
  return "border-warning/25 bg-warning/15 text-warning";
}

export function MeetingCard({ meeting }: { meeting: Meeting }) {
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [keyPoints, setKeyPoints] = useState<string[]>([]);
  const [actionItems, setActionItems] = useState<string[]>([]);

  const generateSummary = async () => {
    try {
      setLoadingSummary(true);
      const payload = await meetingsService.summarizeMeeting(meeting.id);
      setSummary(payload.summary || "Summary unavailable");
      setKeyPoints(payload.key_points || []);
      setActionItems(payload.action_items || []);
      toast.success("AI summary generated");
    } catch {
      toast.error("Unable to generate AI summary for this meeting");
    } finally {
      setLoadingSummary(false);
    }
  };

  return (
    <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/95 transition hover:-translate-y-0.5 hover:shadow-elevated">
      <div className="flex items-start justify-between gap-4">
        <div>
          <CardTitle>{meeting.title}</CardTitle>
          <CardDescription>{meeting.description || "No description"}</CardDescription>
        </div>
        <Badge className={statusClass(meeting.status)}>{meeting.status}</Badge>
      </div>
      <div className="text-sm text-muted-foreground">
        {formatDateTime(meeting.start_time)} → {formatDateTime(meeting.end_time)}
      </div>
      {meeting.google_meet_link && (
        <a href={meeting.google_meet_link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/85">
          Open Google Meet <ExternalLink className="h-4 w-4" />
        </a>
      )}

      <div className="pt-1">
        <Button variant="outline" size="sm" onClick={() => generateSummary().catch(() => null)} disabled={loadingSummary}>
          {loadingSummary ? "Generating..." : "Get AI Summary"}
        </Button>
      </div>

      {summary && (
        <div className="space-y-2 rounded-xl border border-border/70 bg-surface/40 p-3 text-sm">
          <p className="font-medium text-foreground">Summary</p>
          <p className="text-muted-foreground">{summary}</p>
          {keyPoints.length > 0 && (
            <div>
              <p className="font-medium text-foreground">Key Points</p>
              <ul className="list-disc pl-5 text-muted-foreground">
                {keyPoints.map((point, idx) => (
                  <li key={`${meeting.id}-kp-${idx}`}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {actionItems.length > 0 && (
            <div>
              <p className="font-medium text-foreground">Action Items</p>
              <ul className="list-disc pl-5 text-muted-foreground">
                {actionItems.map((item, idx) => (
                  <li key={`${meeting.id}-ai-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
