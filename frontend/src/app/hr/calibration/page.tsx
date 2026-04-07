"use client";

import { useEffect, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { hrService } from "@/services/hr";
import type { HRCalibrationPayload } from "@/types";

export default function HRCalibrationPage() {
  const [payload, setPayload] = useState<HRCalibrationPayload | null>(null);

  useEffect(() => {
    hrService.getCalibration().then(setPayload).catch(() => setPayload(null));
  }, []);

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Calibration</h1>
        <p className="text-sm text-muted-foreground">Compare manager rating behavior and detect potential calibration bias.</p>
      </div>

      <Card>
        <CardTitle>Manager vs Manager Ratings</CardTitle>
        <CardDescription>Bias signal is based on delta from organization average rating.</CardDescription>
        <div className="mt-4 space-y-2">
          {(payload?.managers || []).map((item) => (
            <div key={item.manager_id} className="rounded-md border border-border/70 p-3">
              <p className="font-medium text-foreground">{item.manager_name}</p>
              <p className="text-sm text-muted-foreground">
                Avg: {item.avg_rating} | Org Avg: {item.org_avg_rating} | Delta: {item.delta}
              </p>
              <p className={`text-sm ${item.bias_direction.includes("Higher") ? "text-amber-500" : item.bias_direction.includes("Lower") ? "text-blue-500" : "text-emerald-500"}`}>
                {item.bias_direction}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
