"use client";

import { useCallback, useEffect, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { resolveTrainingFocus } from "@/lib/training-focus";
import { hrService } from "@/services/hr";
import type { HREmployeeDirectoryItem, HREmployeeProfile, HRManagerOption } from "@/types";

export default function HREmployeeDirectoryPage() {
  const [employees, setEmployees] = useState<HREmployeeDirectoryItem[]>([]);
  const [managers, setManagers] = useState<HRManagerOption[]>([]);
  const [selectedManager, setSelectedManager] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [selectedProfile, setSelectedProfile] = useState<HREmployeeProfile | null>(null);
  const [showTrainingOnly, setShowTrainingOnly] = useState(false);

  const load = useCallback(async () => {
    const [employeesData, managersData] = await Promise.all([
      hrService.getEmployees({
        manager_id: selectedManager || undefined,
        department: selectedDepartment || undefined,
        needs_training: showTrainingOnly ? true : undefined,
      }),
      hrService.getManagers(),
    ]);
    setEmployees(employeesData);
    setManagers(managersData);
  }, [selectedDepartment, selectedManager, showTrainingOnly]);

  useEffect(() => {
    load().catch(() => null);
  }, [load]);

  const openProfile = async (employeeId: string) => {
    const profile = await hrService.getEmployeeProfile(employeeId);
    setSelectedProfile(profile);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Employee Directory</h1>
        <p className="text-sm text-muted-foreground">Browse every employee and drill into goals, check-ins, ratings, and AI training guidance.</p>
      </div>

      <Card className="rounded-2xl border border-border/75 bg-card/95">
        <CardTitle>Filters</CardTitle>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-4">
          <Input placeholder="Department" value={selectedDepartment} onChange={(event) => setSelectedDepartment(event.target.value)} />
          <select
            className="h-10 rounded-md border border-input bg-card px-3 text-sm text-foreground"
            value={selectedManager}
            onChange={(event) => setSelectedManager(event.target.value)}
          >
            <option value="">All Managers</option>
            {managers.map((manager) => (
              <option key={manager.id} value={manager.id}>{manager.name}</option>
            ))}
          </select>
          <Button variant={showTrainingOnly ? "default" : "outline"} onClick={() => setShowTrainingOnly((prev) => !prev)}>
            {showTrainingOnly ? "Showing Needs Training" : "Show Needs Training Only"}
          </Button>
          <Button variant="outline" onClick={() => load().catch(() => null)}>Refresh</Button>
        </div>
      </Card>

      <Card className="rounded-2xl border border-border/75 bg-card/95">
        <div className="flex items-center justify-between gap-3 border-b border-border/60 px-4 py-4">
          <div>
            <CardTitle>Employee Records</CardTitle>
            <CardDescription>Structured view of employees, their reporting line, performance, and training status.</CardDescription>
          </div>
          <p className="text-sm text-muted-foreground">{employees.length} record{employees.length === 1 ? "" : "s"}</p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border/60 text-left text-sm">
            <thead className="bg-muted/30 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Employee</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Department</th>
                <th className="px-4 py-3 font-medium">Manager</th>
                <th className="px-4 py-3 font-medium">Progress</th>
                <th className="px-4 py-3 font-medium">Rating</th>
                <th className="px-4 py-3 font-medium">Training</th>
                <th className="px-4 py-3 font-medium">Training Focus</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {employees.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-muted-foreground" colSpan={9}>
                    No employees found for the current filters.
                  </td>
                </tr>
              ) : (
                employees.map((employee) => (
                  <tr key={employee.id} className="align-top transition-colors hover:bg-muted/20">
                    <td className="px-4 py-4">
                      <p className="font-medium text-foreground">{employee.name}</p>
                    </td>
                    <td className="px-4 py-4 text-muted-foreground">{employee.role}</td>
                    <td className="px-4 py-4 text-muted-foreground">{employee.department}</td>
                    <td className="px-4 py-4 text-muted-foreground">{employee.manager_name || "Unassigned"}</td>
                    <td className="px-4 py-4 text-muted-foreground">{employee.progress}%</td>
                    <td className="px-4 py-4 text-muted-foreground">{employee.rating ?? "N/A"}</td>
                    <td className={employee.needs_training ? "px-4 py-4 font-medium text-destructive" : "px-4 py-4 font-medium text-emerald-500"}>
                      {employee.needs_training ? "YES" : "NO"}
                    </td>
                    <td className="px-4 py-4 text-muted-foreground">
                      {employee.needs_training
                        ? resolveTrainingFocus({
                            progress: Number(employee.progress ?? 0),
                            consistency: Number(employee.consistency ?? 0),
                            rating: Number(employee.rating ?? 0),
                            needsTraining: Boolean(employee.needs_training),
                          })
                        : "-"}
                    </td>
                    <td className="px-4 py-4">
                      <Button size="sm" onClick={() => openProfile(employee.id).catch(() => null)}>Open Profile</Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {selectedProfile ? (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40">
          <div className="h-full w-full max-w-2xl overflow-y-auto bg-background p-6 shadow-2xl">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold text-foreground">{selectedProfile.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {selectedProfile.role} · {selectedProfile.department} · Manager: {selectedProfile.manager_name || "Unassigned"}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => setSelectedProfile(null)}>Close</Button>
            </div>

            <div className="mt-4 space-y-4">
              <Card className="rounded-xl border border-border/75 bg-card/95">
                <CardTitle className="text-base">AI Training Decision</CardTitle>
                <CardDescription>{selectedProfile.ai_training_reason}</CardDescription>
                <p className="mt-2 text-xs text-muted-foreground">
                  Primary training type: {resolveTrainingFocus({
                    reason: selectedProfile.ai_training_reason,
                    progress: Number(selectedProfile.progress ?? 0),
                    consistency: Number(selectedProfile.consistency ?? 0),
                    rating: Number(selectedProfile.avg_rating ?? 0),
                    needsTraining: Boolean(selectedProfile.needs_training),
                  })}
                </p>
              </Card>

              <Card className="rounded-xl border border-border/75 bg-card/95">
                <CardTitle className="text-base">Goals</CardTitle>
                <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                  {selectedProfile.goals.map((goal) => (
                    <p key={goal.id}>{goal.title} · {goal.progress}% · {goal.status}</p>
                  ))}
                </div>
              </Card>

              <Card className="rounded-xl border border-border/75 bg-card/95">
                <CardTitle className="text-base">Check-ins</CardTitle>
                <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                  {selectedProfile.checkins.map((checkin) => (
                    <p key={checkin.id}>
                      {checkin.progress}% · {checkin.status} · {new Date(checkin.created_at).toLocaleDateString()} · {checkin.manager_feedback || "No feedback"}
                    </p>
                  ))}
                </div>
              </Card>

              <Card className="rounded-xl border border-border/75 bg-card/95">
                <CardTitle className="text-base">Ratings</CardTitle>
                <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                  {selectedProfile.ratings.map((rating) => (
                    <p key={rating.id}>{rating.rating_label} ({rating.rating}) · {rating.comments || "No comment"}</p>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
