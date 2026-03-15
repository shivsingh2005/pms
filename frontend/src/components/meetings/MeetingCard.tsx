import { ExternalLink } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";
import { Meeting } from "@/types";

function statusClass(status: Meeting["status"]) {
  if (status === "completed") return "bg-success/15 text-success";
  if (status === "cancelled") return "bg-error/15 text-error";
  return "bg-warning/15 text-warning";
}

export function MeetingCard({ meeting }: { meeting: Meeting }) {
  return (
    <Card className="space-y-3 transition hover:-translate-y-0.5">
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
    </Card>
  );
}
