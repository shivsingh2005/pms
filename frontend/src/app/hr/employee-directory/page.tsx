"use client";

import { useCallback, useEffect, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {employees.map((employee) => (
          <Card key={employee.id} className="space-y-2 rounded-xl border border-border/75 bg-card/95">
            <CardTitle className="text-lg">{employee.name}</CardTitle>
            <CardDescription>{employee.role} · {employee.department}</CardDescription>
            <p className="text-sm text-muted-foreground">Manager: {employee.manager_name || "Unassigned"}</p>
            <p className="text-sm text-muted-foreground">Progress: {employee.progress}% · Rating: {employee.rating ?? "N/A"}</p>
            <p className={`text-xs ${employee.needs_training ? "text-destructive" : "text-emerald-500"}`}>
              Needs Training: {employee.needs_training ? "YES" : "NO"}
            </p>
            <Button size="sm" onClick={() => openProfile(employee.id).catch(() => null)}>Open Profile</Button>
          </Card>
        ))}
      </div>

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
