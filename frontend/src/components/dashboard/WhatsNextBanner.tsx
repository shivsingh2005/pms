"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { dashboardService } from "@/services/dashboard";
import { useSessionStore } from "@/store/useSessionStore";
import {
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Clock,
  Target,
  Zap,
} from "lucide-react";

interface NextActionData {
  action: string;
  message: string;
  priority: "high" | "medium" | "low";
  cta: string;
  url: string | null;
}

/**
 * What's Next Banner
 *
 * PRD FIX 12: One clear next action for every user on every dashboard.
 * Computed from user's performance cycle state.
 * Context-aware, not a generic to-do list.
 *
 * Priority determines visual style:
 * - High: Red alert, needs immediate attention
 * - Medium: Amber, can wait a few days
 * - Low: Green, all good for now
 */
export function WhatsNextBanner() {
  const user = useSessionStore((state) => state.user);
  const canShowNextAction = Boolean(user?.id) && user?.role !== "hr" && user?.role !== "leadership";

  const nextActionQuery = useQuery({
    queryKey: ["dashboard-next-action", user?.id],
    enabled: canShowNextAction,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    queryFn: async () => {
      const data = await dashboardService.getNextAction();

      return {
        action: data.action_label?.toLowerCase().replaceAll(" ", "_") || "on_track",
        message: data.detail || data.title,
        priority: data.level === "critical" ? "high" : data.level === "warning" ? "medium" : "low",
        cta: data.action_label || "Open",
        url: data.action_url || null,
      } satisfies NextActionData;
    },
  });

  const nextAction = nextActionQuery.data ?? null;

  // HR and leadership portals do not use performance cycle "next action" nudges.
  if (user?.role === "hr" || user?.role === "leadership") {
    return null;
  }

  if (nextActionQuery.isLoading || !nextAction) {
    return null;
  }

  // Return null if user is on track (show only when action needed)
  if (nextAction.action === "on_track") {
    return (
      <Card className="border-emerald-200/50 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/20">
        <div className="flex items-center gap-4 p-4">
          <CheckCircle2 className="h-6 w-6 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div className="flex-1">
            <p className="font-semibold text-emerald-900 dark:text-emerald-100">
              {nextAction.message}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Determine visual style based on priority
  const priorityStyles = {
    high: {
      container: "border-red-200/50 bg-red-50 dark:border-red-900/50 dark:bg-red-950/20",
      icon: "text-red-600 dark:text-red-400",
      title: "text-red-900 dark:text-red-100",
      button: "bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800",
    },
    medium: {
      container: "border-amber-200/50 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/20",
      icon: "text-amber-600 dark:text-amber-400",
      title: "text-amber-900 dark:text-amber-100",
      button: "bg-amber-600 hover:bg-amber-700 dark:bg-amber-700 dark:hover:bg-amber-800",
    },
    low: {
      container: "border-cyan-200/50 bg-cyan-50 dark:border-cyan-900/50 dark:bg-cyan-950/20",
      icon: "text-cyan-600 dark:text-cyan-400",
      title: "text-cyan-900 dark:text-cyan-100",
      button: "bg-cyan-600 hover:bg-cyan-700 dark:bg-cyan-700 dark:hover:bg-cyan-800",
    },
  };

  const style = priorityStyles[nextAction.priority];

  // Select icon based on action
  const IconMap = {
    create_goals: Target,
    submit_goals: Zap,
    wait_approval: Clock,
    submit_checkin: AlertCircle,
    review_pending: AlertCircle,
    on_track: CheckCircle2,
  };

  const IconComponent =
    IconMap[nextAction.action as keyof typeof IconMap] || AlertCircle;

  return (
    <Card className={`border ${style.container}`}>
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <IconComponent className={`h-6 w-6 flex-shrink-0 ${style.icon}`} />
          <div className="flex-1">
            <div className="mb-1 inline-block rounded-full bg-white/40 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide opacity-80">
              {nextAction.priority === "high"
                ? "⚡ Action Required"
                : nextAction.priority === "medium"
                  ? "⏳ Coming Up"
                  : "✓ Optional"}
            </div>
            <p className={`font-semibold ${style.title}`}>
              {nextAction.message}
            </p>
          </div>
        </div>

        {nextAction.url && (
          <a href={nextAction.url} className="inline-flex">
            <Button className={`flex-shrink-0 gap-2 text-white ${style.button}`}>
              {nextAction.cta}
              <ChevronRight className="h-4 w-4" />
            </Button>
          </a>
        )}
      </div>
    </Card>
  );
}
