"use client";

import React from "react";

/**
 * Smart Pre-fill System
 *
 * PRD FIX 10: Automatically pre-fill forms with previous data.
 * Users only type NEW information, not repeated values.
 *
 * Rules:
 * - Check-in form: Pre-fill goal progress from last check-in
 * - Check-in form: Pre-fill RAG status as 🟢 (user changes if not on track)
 * - Check-in form: Pre-fill blockers if still unresolved
 * - Rating form: Pre-fill with AI suggestion (user only changes if they disagree)
 * - Goal creation: Pre-fill weightage with AI suggestion
 * - Goal creation: Pre-fill KPI from library
 * - Meeting scheduling: Pre-fill participants (emp + manager)
 * - Meeting scheduling: Pre-fill duration as 30 min
 * - Meeting scheduling: Pre-fill title as "Check-in: {employee name}"
 */

interface PreFillData {
  fieldName: string;
  value: any;
  source: "last_submission" | "ai_suggestion" | "library" | "context";
  confidence: "high" | "medium" | "low";
}

/**
 * Fetches pre-fill data for a form
 * @param formType - Type of form (checkin | rating | goal | meeting)
 * @param context - Additional context (employee_id, goal_id, etc)
 */
export async function getPrefillData(
  formType: "checkin" | "rating" | "goal" | "meeting",
  context: Record<string, string>
): Promise<PreFillData[]> {
  try {
    const response = await fetch("/api/v1/forms/prefill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ form_type: formType, context }),
    });

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Failed to fetch pre-fill data:", error);
  }

  return [];
}

/**
 * Hook for managing pre-filled form state
 * Combines pre-filled values with user edits
 */
export function usePrefilledForm<T extends Record<string, any>>(
  initialData: T,
  isPrefilled: Record<keyof T, boolean> = {} as Record<keyof T, boolean>
) {
  const [values, setValues] = React.useState(initialData);
  const [edited, setEdited] = React.useState<Set<keyof T>>(new Set());

  const updateValue = (field: keyof T, value: any) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    setEdited((prev) => new Set(prev).add(field));
  };

  const resetToInitial = (field: keyof T) => {
    setValues((prev) => ({ ...prev, [field]: initialData[field] }));
    setEdited((prev) => {
      const next = new Set(prev);
      next.delete(field);
      return next;
    });
  };

  return {
    values,
    updateValue,
    resetToInitial,
    edited,
    isUnedited: (field: keyof T) => !edited.has(field),
    isPrefilled: (field: keyof T) => isPrefilled[field] ?? false,
  };
}

/**
 * Visual indicator for pre-filled field
 * Shows small badge indicating field is pre-filled
 */
export function PrefilledIndicator({ 
  source,
  onClick,
}: { 
  source: "ai" | "previous" | "library";
  onClick?: () => void;
}) {
  const labels = {
    ai: "✨ AI suggested",
    previous: "↻ From last time",
    library: "📚 Template",
  };

  return (
    <button
      onClick={onClick}
      type="button"
      className="text-xs font-medium text-muted-foreground hover:text-foreground cursor-help"
      title="Click to reset to original value"
    >
      {labels[source]}
    </button>
  );
}

/**
 * Pre-filled text input wrapper
 * Shows visual distinction for pre-filled values
 */
export function PrefilledInput({
  label,
  value,
  onChange,
  isPrefilled,
  sourceType,
  onReset,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  value: string;
  onChange: (value: string) => void;
  isPrefilled: boolean;
  sourceType?: "ai" | "previous" | "library";
  onReset?: () => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        {isPrefilled && sourceType && (
          <PrefilledIndicator source={sourceType} onClick={onReset} />
        )}
      </div>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-lg border px-3 py-2 text-sm transition-colors ${
          isPrefilled
            ? "border-amber-300/50 bg-amber-50/30 dark:border-amber-800/40 dark:bg-amber-950/20"
            : "border-input bg-card"
        } text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand`}
      />
    </div>
  );
}

/**
 * Pre-filled textarea wrapper
 */
export function PrefilledTextarea({
  label,
  value,
  onChange,
  isPrefilled,
  sourceType,
  onReset,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  value: string;
  onChange: (value: string) => void;
  isPrefilled: boolean;
  sourceType?: "ai" | "previous" | "library";
  onReset?: () => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        {isPrefilled && sourceType && (
          <PrefilledIndicator source={sourceType} onClick={onReset} />
        )}
      </div>
      <textarea
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-lg border px-3 py-2 text-sm transition-colors ${
          isPrefilled
            ? "border-amber-300/50 bg-amber-50/30 dark:border-amber-800/40 dark:bg-amber-950/20"
            : "border-input bg-card"
        } text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand`}
      />
    </div>
  );
}

/**
 * Helper to determine if a value was changed from its initial state
 */
export function hasValueChanged<T>(initial: T, current: T): boolean {
  if (typeof initial === "object" && typeof current === "object") {
    return JSON.stringify(initial) !== JSON.stringify(current);
  }
  return initial !== current;
}
