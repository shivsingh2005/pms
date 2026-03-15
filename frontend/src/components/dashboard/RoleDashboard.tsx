"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardTitle } from "@/components/ui/card";
import { HeatmapGrid } from "@/components/dashboard/HeatmapGrid";
import { StackRankingTable } from "@/components/dashboard/StackRankingTable";
import { ProgressRing } from "@/components/dashboard/ProgressRing";
import type { UserRole } from "@/types";

const trend = [
  { name: "Q1", score: 72 },
  { name: "Q2", score: 76 },
  { name: "Q3", score: 81 },
  { name: "Q4", score: 84 },
];

const distribution = [
  { name: "EE", value: 12 },
  { name: "DE", value: 22 },
  { name: "ME", value: 43 },
  { name: "SME", value: 18 },
  { name: "NI", value: 5 },
];

export function RoleDashboard({ role }: { role: UserRole }) {
  if (role === "employee") {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
        <Card className="transition hover:-translate-y-0.5 md:col-span-4">
          <CardTitle>My Progress</CardTitle>
          <div className="mt-6 flex items-center justify-center"><ProgressRing value={78} /></div>
        </Card>
        <Card className="transition hover:-translate-y-0.5 md:col-span-8">
          <CardTitle>Performance Trend</CardTitle>
          <div className="mt-4 h-64 rounded-xl border bg-muted/20 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }} />
                <Legend verticalAlign="bottom" align="center" iconType="circle" />
                <Area type="monotone" dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--secondary) / 0.24)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    );
  }

  if (role === "manager") {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
        <Card className="transition hover:-translate-y-0.5 md:col-span-5">
          <CardTitle>Team Progress Heatmap</CardTitle>
          <div className="mt-4">
            <HeatmapGrid values={[65, 72, 90, 44, 85, 78, 66, 81, 88, 62, 58, 74, 79, 92]} />
          </div>
        </Card>
        <Card className="transition hover:-translate-y-0.5 md:col-span-7">
          <CardTitle>Stack Ranking</CardTitle>
          <div className="mt-4">
            <StackRankingTable rows={[{ name: "Ariana", score: 91, trend: "up" }, { name: "Rahul", score: 87, trend: "up" }, { name: "Karan", score: 79, trend: "flat" }, { name: "Meera", score: 74, trend: "down" }]} />
          </div>
        </Card>
      </div>
    );
  }

  if (role === "hr") {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
        <Card className="transition hover:-translate-y-0.5 md:col-span-7">
          <CardTitle>Rating Calibration</CardTitle>
          <div className="mt-4 h-64 rounded-xl border bg-muted/20 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }} />
                <Legend verticalAlign="bottom" align="center" iconType="circle" />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card className="transition hover:-translate-y-0.5 md:col-span-5">
          <CardTitle>Training Need Heatmap</CardTitle>
          <div className="mt-4">
            <HeatmapGrid values={[30, 45, 61, 53, 29, 71, 88, 67, 50, 39, 64, 75, 82, 40]} />
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
      <Card className="transition hover:-translate-y-0.5 md:col-span-8">
        <CardTitle>Company Performance Trends</CardTitle>
        <div className="mt-4 h-64 rounded-xl border bg-muted/20 p-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }} />
              <Legend verticalAlign="bottom" align="center" iconType="circle" />
              <Area type="monotone" dataKey="score" stroke="hsl(var(--secondary))" fill="hsl(var(--secondary) / 0.25)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card className="transition hover:-translate-y-0.5 md:col-span-4">
        <CardTitle>Talent Pipeline Snapshot</CardTitle>
        <div className="mt-4">
          <StackRankingTable rows={[{ name: "High Potential Pool", score: 26, trend: "up" }, { name: "Succession Ready", score: 14, trend: "flat" }, { name: "Attrition Risk", score: 8, trend: "down" }]} />
        </div>
      </Card>
    </div>
  );
}
