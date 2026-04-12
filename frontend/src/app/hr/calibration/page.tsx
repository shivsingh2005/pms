"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { hrService } from "@/services/hr";
import type { HRCalibrationPayload } from "@/types";

function formatDate(value?: string | null): string {
  if (!value) return "No check-in on record";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function biasTone(label: string): string {
  if (label.includes("Higher")) return "text-amber-500";
  if (label.includes("Lower")) return "text-blue-500";
  return "text-emerald-500";
}

export default function HRCalibrationPage() {
  const [payload, setPayload] = useState<HRCalibrationPayload | null>(null);
  const [expandedManagerId, setExpandedManagerId] = useState<string | null>(null);

  useEffect(() => {
    hrService.getCalibration().then(setPayload).catch(() => setPayload(null));
  }, []);

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Calibration</h1>
        <p className="text-sm text-muted-foreground">Compare manager rating behavior against the organization baseline using live team, goal, rating, and check-in data.</p>
      </div>

      <Card className="space-y-4 rounded-2xl border border-border/75 bg-card/95 p-4">
        <CardTitle>Organization Calibration Snapshot</CardTitle>
        <CardDescription>Built from original rating and check-in records, not placeholder values.</CardDescription>
        <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <Metric label="Managers" value={payload?.summary?.total_managers ?? payload?.managers.length ?? 0} />
          <Metric label="Employees" value={payload?.summary?.total_employees ?? 0} />
          <Metric label="Team Members Tracked" value={payload?.summary?.total_team_members ?? 0} />
          <Metric label="Org Avg Rating" value={(payload?.summary?.org_avg_rating ?? 0).toFixed(2)} />
          <Metric label="At-Risk Employees" value={payload?.summary?.at_risk_employees ?? 0} />
        </div>
        <p className="text-xs text-muted-foreground">Generated {payload?.generated_at ? formatDate(payload.generated_at) : "just now"}</p>
      </Card>

      <Card>
        <CardTitle>Manager Calibration Detail</CardTitle>
        <CardDescription>Each manager card starts with a short summary. Use the detail button to reveal the underlying direct-report data.</CardDescription>
        <div className="mt-4 space-y-4">
          {(payload?.managers || []).map((item) => (
            <div key={item.manager_id} className="rounded-xl border border-border/70 bg-muted/10 p-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-base font-semibold text-foreground">{item.manager_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.department || "General"} · Team size {item.team_size ?? item.members?.length ?? 0}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{item.bias_direction}</p>
                  <p className={`text-sm ${biasTone(item.bias_direction)}`}>Delta {item.delta >= 0 ? "+" : ""}{item.delta.toFixed(2)}</p>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
                <CompactStat label="Avg Rating" value={item.avg_rating.toFixed(2)} />
                <CompactStat label="Org Avg" value={item.org_avg_rating.toFixed(2)} />
                <CompactStat label="Avg Progress" value={`${(item.avg_progress ?? 0).toFixed(1)}%`} />
                <CompactStat label="Consistency" value={`${(item.consistency ?? 0).toFixed(1)}%`} />
                <CompactStat label="At Risk" value={item.at_risk_employees ?? 0} />
                <CompactStat label="Last Check-in" value={formatDate(item.last_checkin)} wide />
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setExpandedManagerId((current) => (current === item.manager_id ? null : item.manager_id))}
                >
                  {expandedManagerId === item.manager_id ? "Hide details" : "Show details"}
                </Button>
                <p className="text-xs text-muted-foreground">Showing {item.team_size ?? item.members?.length ?? 0} direct reports when expanded.</p>
              </div>

              {expandedManagerId === item.manager_id ? (
                <div className="mt-4 space-y-4">
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    <div className="rounded-lg border border-border/60 bg-card p-3">
                      <p className="text-sm font-medium text-foreground">Top Performers</p>
                      <div className="mt-2 space-y-2">
                        {(item.top_performers || []).slice(0, 3).map((member) => (
                          <SourceRow
                            key={`top-${item.manager_id}-${member.id}`}
                            name={member.name}
                            meta={`Progress ${Number(member.progress ?? 0).toFixed(1)}% · Rating ${Number(member.rating ?? 0).toFixed(2)}`}
                            submeta={member.last_checkin ? `Last check-in ${formatDate(member.last_checkin)}` : "Last check-in not available"}
                          />
                        ))}
                        {!item.top_performers?.length ? <p className="text-xs text-muted-foreground">No performer data available.</p> : null}
                      </div>
                    </div>

                    <div className="rounded-lg border border-border/60 bg-card p-3">
                      <p className="text-sm font-medium text-foreground">Low Performers</p>
                      <div className="mt-2 space-y-2">
                        {(item.low_performers || []).slice(0, 3).map((member) => (
                          <SourceRow
                            key={`low-${item.manager_id}-${member.id}`}
                            name={member.name}
                            meta={`Progress ${Number(member.progress ?? 0).toFixed(1)}% · Rating ${Number(member.rating ?? 0).toFixed(2)}`}
                            submeta={member.last_checkin ? `Last check-in ${formatDate(member.last_checkin)}` : "Last check-in not available"}
                          />
                        ))}
                        {!item.low_performers?.length ? <p className="text-xs text-muted-foreground">No low performer data available.</p> : null}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-border/60 bg-card p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-foreground">Original Direct-Report Data</p>
                      <span className="text-xs text-muted-foreground">{item.members?.length ?? 0} records</span>
                    </div>
                    <div className="mt-3 overflow-x-auto">
                      <table className="min-w-full text-left text-xs">
                        <thead className="text-muted-foreground">
                          <tr>
                            <th className="py-2 pr-4 font-medium">Employee</th>
                            <th className="py-2 pr-4 font-medium">Progress</th>
                            <th className="py-2 pr-4 font-medium">Rating</th>
                            <th className="py-2 pr-4 font-medium">Consistency</th>
                            <th className="py-2 pr-4 font-medium">Last Check-in</th>
                            <th className="py-2 pr-4 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(item.members || []).map((member) => (
                            <tr key={`${item.manager_id}-${member.id}`} className="border-t border-border/60">
                              <td className="py-2 pr-4 text-foreground">{member.name}</td>
                              <td className="py-2 pr-4">{Number(member.progress ?? 0).toFixed(1)}%</td>
                              <td className="py-2 pr-4">{Number(member.rating ?? 0).toFixed(2)}</td>
                              <td className="py-2 pr-4">{Number(member.consistency ?? 0).toFixed(1)}%</td>
                              <td className="py-2 pr-4">{formatDate(member.last_checkin)}</td>
                              <td className="py-2 pr-4">{member.status}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/70 p-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}

function CompactStat({ label, value, wide = false }: { label: string; value: string | number; wide?: boolean }) {
  return (
    <div className={`rounded-lg border border-border/60 bg-background/70 p-3 ${wide ? "md:col-span-2 xl:col-span-2" : ""}`}>
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function SourceRow({ name, meta, submeta }: { name: string; meta: string; submeta: string }) {
  return (
    <div className="rounded-md border border-border/60 bg-muted/20 p-2">
      <p className="text-sm font-medium text-foreground">{name}</p>
      <p className="text-xs text-muted-foreground">{meta}</p>
      <p className="text-[11px] text-muted-foreground">{submeta}</p>
    </div>
  );
}
