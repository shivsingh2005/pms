"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";

const steps = [
  { title: "Goal Creation", detail: "Define SMART goals and align to organization objective." },
  { title: "Goal Approval", detail: "Manager reviews and approves goal weightage and KPIs." },
  { title: "Check-ins", detail: "Run periodic check-ins and update progress evidence." },
  { title: "Review", detail: "Collect manager review and identify growth opportunities." },
  { title: "Cycle Closed", detail: "Finalize score, reflection and next cycle planning." },
];

export function GoalTimeline() {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <motion.div key={step.title} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.08 }} className="relative pl-8">
          <div className="absolute left-2 top-2 h-full w-px bg-border" />
          <div className="absolute left-0 top-1 h-4 w-4 rounded-full border-2 border-primary bg-card" />
          <Card>
            <div className="text-sm font-semibold text-foreground">{step.title}</div>
            <div className="mt-1 text-sm text-muted-foreground">{step.detail}</div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
