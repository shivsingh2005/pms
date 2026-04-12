type TrainingFocus = "AI" | "Communication" | "Execution" | "Leadership" | "Technical" | "Collaboration";

const REASON_KEYWORDS: Array<{ focus: TrainingFocus; keywords: string[] }> = [
  { focus: "AI", keywords: ["ai", "automation", "prompt", "ml", "machine learning"] },
  { focus: "Communication", keywords: ["communication", "stakeholder", "presentation", "narrative", "clarity"] },
  { focus: "Leadership", keywords: ["leadership", "coaching", "mentoring", "ownership", "decision"] },
  { focus: "Technical", keywords: ["technical", "architecture", "coding", "code", "engineering", "system design"] },
  { focus: "Execution", keywords: ["execution", "delivery", "planning", "prioritization", "deadline"] },
  { focus: "Collaboration", keywords: ["collaboration", "cross-functional", "teamwork", "alignment"] },
];

export function inferTrainingFocusFromReason(reason?: string | null): TrainingFocus | null {
  const text = String(reason || "").toLowerCase();
  if (!text) return null;

  for (const group of REASON_KEYWORDS) {
    if (group.keywords.some((keyword) => text.includes(keyword))) {
      return group.focus;
    }
  }

  return null;
}

export function inferTrainingFocusFromMetrics(input: {
  progress: number;
  consistency: number;
  rating: number;
  needsTraining: boolean;
}): TrainingFocus | null {
  if (!input.needsTraining) return null;

  if (input.rating <= 2.5) return "AI";
  if (input.consistency < 55) return "Communication";
  if (input.progress < 45) return "Execution";
  if (input.rating < 3.2) return "Technical";
  if (input.consistency < 70) return "Collaboration";
  return "Leadership";
}

export function resolveTrainingFocus(input: {
  reason?: string | null;
  progress: number;
  consistency: number;
  rating: number;
  needsTraining: boolean;
}): string {
  const byReason = inferTrainingFocusFromReason(input.reason);
  if (byReason) return byReason;
  return inferTrainingFocusFromMetrics(input) || "General";
}

export function summarizeTopTrainingFocus(focuses: string[]): string {
  if (!focuses.length) return "General";
  const counts = new Map<string, number>();
  for (const focus of focuses) {
    counts.set(focus, (counts.get(focus) || 0) + 1);
  }
  const sorted = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  return sorted[0][0];
}
