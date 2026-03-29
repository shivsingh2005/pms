"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { adminService } from "@/services/admin";
import { useSessionStore } from "@/store/useSessionStore";
import type { AdminAuditLog, AdminSystemSettings } from "@/types";

export default function AdminSettingsPage() {
  const user = useSessionStore((state) => state.user);
  const [activeSection, setActiveSection] = useState<"system" | "ai" | "audit">("system");
  const [settings, setSettings] = useState<AdminSystemSettings | null>(null);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);

  const [workStart, setWorkStart] = useState("09:00");
  const [workEnd, setWorkEnd] = useState("18:00");
  const [timezone, setTimezone] = useState("UTC");

  const [ratingMin, setRatingMin] = useState("1");
  const [ratingMax, setRatingMax] = useState("5");
  const [ratingLabels, setRatingLabels] = useState('{"1":"NI","2":"SME","3":"ME","4":"DE","5":"EE"}');

  const [frequencyMode, setFrequencyMode] = useState("weekly");
  const [frequencyDays, setFrequencyDays] = useState("Friday");

  const [aiProvider, setAiProvider] = useState("gemini");
  const [aiModel, setAiModel] = useState("gemini-2.5-flash");
  const [aiApiKey, setAiApiKey] = useState("");

  const load = async () => {
    const [settingsRes, logsRes] = await Promise.all([adminService.getSettings(), adminService.getAuditLogs(80)]);
    setSettings(settingsRes);
    setAuditLogs(logsRes);

    const workingHours = settingsRes.working_hours || {};
    setWorkStart(String(workingHours.start || "09:00"));
    setWorkEnd(String(workingHours.end || "18:00"));
    setTimezone(String(workingHours.timezone || "UTC"));

    const ratingScale = settingsRes.rating_scale || {};
    setRatingMin(String(ratingScale.min || 1));
    setRatingMax(String(ratingScale.max || 5));
    setRatingLabels(JSON.stringify(ratingScale.labels || { "1": "NI", "2": "SME", "3": "ME", "4": "DE", "5": "EE" }));

    const checkinFrequency = settingsRes.checkin_frequency || {};
    setFrequencyMode(String(checkinFrequency.mode || "weekly"));
    setFrequencyDays(Array.isArray(checkinFrequency.days) ? checkinFrequency.days.join(",") : "Friday");

    const aiSettings = settingsRes.ai_settings || {};
    setAiProvider(String(aiSettings.provider || "gemini"));
    setAiModel(String(aiSettings.model || "gemini-2.5-flash"));
  };

  useEffect(() => {
    if (user) {
      load().catch(() => null);
    }
  }, [user]);

  const saveSystemSettings = async () => {
    let parsedLabels: Record<string, string> = {};
    try {
      parsedLabels = JSON.parse(ratingLabels);
    } catch {
      parsedLabels = { "1": "NI", "2": "SME", "3": "ME", "4": "DE", "5": "EE" };
    }

    await adminService.updateSettings({
      working_hours: {
        start: workStart,
        end: workEnd,
        timezone,
      },
      rating_scale: {
        min: Number(ratingMin),
        max: Number(ratingMax),
        labels: parsedLabels,
      },
      checkin_frequency: {
        mode: frequencyMode,
        days: frequencyDays.split(",").map((item) => item.trim()).filter(Boolean),
      },
    });
    await load();
  };

  const saveAiSettings = async () => {
    await adminService.updateSettings({
      ai_settings: {
        provider: aiProvider,
        model: aiModel,
        api_key: aiApiKey,
      },
    });
    setAiApiKey("");
    await load();
  };

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Settings"
        description="Global platform configuration for scheduling, ratings, check-in cadence, and AI integration."
      />

      <div className="flex flex-wrap gap-2">
        <Button variant={activeSection === "system" ? "default" : "outline"} onClick={() => setActiveSection("system")}>System Config</Button>
        <Button variant={activeSection === "ai" ? "default" : "outline"} onClick={() => setActiveSection("ai")}>AI Settings</Button>
        <Button variant={activeSection === "audit" ? "default" : "outline"} onClick={() => setActiveSection("audit")}>Audit Logs</Button>
      </div>

      {activeSection === "system" ? (
        <Card className="space-y-4">
          <CardTitle>Global Configurations</CardTitle>
          <CardDescription>Control work windows, rating scale mappings, and check-in frequency.</CardDescription>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Input placeholder="Work start" value={workStart} onChange={(event) => setWorkStart(event.target.value)} />
            <Input placeholder="Work end" value={workEnd} onChange={(event) => setWorkEnd(event.target.value)} />
            <Input placeholder="Timezone" value={timezone} onChange={(event) => setTimezone(event.target.value)} />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Input placeholder="Rating min" value={ratingMin} onChange={(event) => setRatingMin(event.target.value)} />
            <Input placeholder="Rating max" value={ratingMax} onChange={(event) => setRatingMax(event.target.value)} />
          </div>

          <Input
            placeholder='Rating labels JSON, e.g. {"1":"NI","2":"SME"}'
            value={ratingLabels}
            onChange={(event) => setRatingLabels(event.target.value)}
          />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <select
              className="h-10 rounded-lg border border-input/90 bg-card px-3 text-sm"
              value={frequencyMode}
              onChange={(event) => setFrequencyMode(event.target.value)}
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
            <Input
              placeholder="Check-in days comma separated"
              value={frequencyDays}
              onChange={(event) => setFrequencyDays(event.target.value)}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={saveSystemSettings}>Save System Settings</Button>
          </div>
        </Card>
      ) : null}

      {activeSection === "ai" ? (
        <Card className="space-y-4">
          <CardTitle>AI Settings</CardTitle>
          <CardDescription>Configure Gemini provider settings and rotate API credentials safely.</CardDescription>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Input placeholder="Provider" value={aiProvider} onChange={(event) => setAiProvider(event.target.value)} />
            <Input placeholder="Model" value={aiModel} onChange={(event) => setAiModel(event.target.value)} />
          </div>

          <Input
            type="password"
            placeholder="New Gemini API key (optional)"
            value={aiApiKey}
            onChange={(event) => setAiApiKey(event.target.value)}
          />

          <p className="text-xs text-muted-foreground">
            Current key: {String(settings?.ai_settings?.api_key_masked || "Not set")}
          </p>

          <div className="flex justify-end">
            <Button onClick={saveAiSettings}>Save AI Settings</Button>
          </div>
        </Card>
      ) : null}

      {activeSection === "audit" ? (
        <Card className="space-y-3">
          <CardTitle>System Audit Logs</CardTitle>
          <CardDescription>Who changed what, with event-level traceability.</CardDescription>
          <div className="max-h-96 space-y-2 overflow-auto">
            {auditLogs.map((entry) => (
              <div key={entry.id} className="rounded-lg border border-border/70 p-3">
                <p className="text-sm font-medium text-foreground">{entry.message}</p>
                <p className="text-xs text-muted-foreground">
                  {entry.action} • {new Date(entry.created_at).toLocaleString()}
                </p>
              </div>
            ))}
            {auditLogs.length === 0 ? <p className="text-sm text-muted-foreground">No audit logs recorded.</p> : null}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
