"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";

import { PageHeader } from "@/components/ui/page-header";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useSessionStore } from "@/store/useSessionStore";
import { performanceCyclesService } from "@/services/performance-cycles";
import { aiService } from "@/services/ai";
import type {
  AIQuarterlyUsage,
  AnnualOperatingPlanItem,
  DepartmentFrameworkPolicy,
  FrameworkRecommendation,
  FrameworkSelection,
  KPILibraryItem,
} from "@/types";

type StrategyTab = "framework" | "policies" | "kpi" | "aop" | "ai-usage";

const tabs: Array<{ key: StrategyTab; label: string }> = [
  { key: "framework", label: "My Framework" },
  { key: "policies", label: "Dept Policies" },
  { key: "kpi", label: "KPI Library" },
  { key: "aop", label: "AOP" },
  { key: "ai-usage", label: "AI Usage" },
];

export default function HRStrategyPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);

  const [activeTab, setActiveTab] = useState<StrategyTab>("framework");

  const [recommendation, setRecommendation] = useState<FrameworkRecommendation | null>(null);
  const [selection, setSelection] = useState<FrameworkSelection | null>(null);
  const [selectedFramework, setSelectedFramework] = useState("OKR");

  const [policies, setPolicies] = useState<DepartmentFrameworkPolicy[]>([]);
  const [policyDepartment, setPolicyDepartment] = useState("");
  const [policyFrameworks, setPolicyFrameworks] = useState("OKR,MBO");

  const [kpiItems, setKpiItems] = useState<KPILibraryItem[]>([]);
  const [kpiRole, setKpiRole] = useState("Backend Engineer");
  const [kpiDomain, setKpiDomain] = useState("Engineering");
  const [kpiDepartment, setKpiDepartment] = useState("Engineering");
  const [kpiTitle, setKpiTitle] = useState("Improve API latency");
  const [kpiDescription, setKpiDescription] = useState("Reduce p95 latency for critical APIs.");
  const [kpiMetric, setKpiMetric] = useState("p95 API latency under 250ms");
  const [kpiWeight, setKpiWeight] = useState(20);
  const [kpiFramework, setKpiFramework] = useState("OKR");

  const [aopItems, setAopItems] = useState<AnnualOperatingPlanItem[]>([]);
  const [aopYear, setAopYear] = useState(new Date().getFullYear());
  const [aopDepartment, setAopDepartment] = useState("Engineering");
  const [aopObjective, setAopObjective] = useState("Increase platform reliability to 99.95%.");
  const [aopTarget, setAopTarget] = useState("99.95 uptime");

  const [usage, setUsage] = useState<AIQuarterlyUsage | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (user.role !== "hr" && user.role !== "leadership") {
      router.push("/unauthorized");
      return;
    }

    void initializeScreen();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, user?.id]);

  const parsedFrameworks = useMemo(
    () => policyFrameworks.split(",").map((item) => item.trim()).filter(Boolean),
    [policyFrameworks],
  );

  const initializeScreen = async () => {
    setLoading(true);
    try {
      const [selectionData, policiesData, kpiData, aopData, usageData] = await Promise.all([
        performanceCyclesService.getFrameworkSelection(),
        performanceCyclesService.listFrameworkPolicies(),
        performanceCyclesService.listKpiLibrary(),
        performanceCyclesService.listAop(),
        aiService.getQuarterlyUsage(),
      ]);

      setSelection(selectionData);
      if (selectionData?.selected_framework) {
        setSelectedFramework(selectionData.selected_framework);
      }
      setPolicies(policiesData);
      setKpiItems(kpiData);
      setAopItems(aopData);
      setUsage(usageData);

      if (user) {
        const recommendationData = await performanceCyclesService.recommendFramework({
          role: user.role,
          department: user.department || undefined,
        });
        setRecommendation(recommendationData);
      }
    } catch {
      toast.error("Failed to load strategy controls");
    } finally {
      setLoading(false);
    }
  };

  const saveFrameworkSelection = async () => {
    try {
      const updated = await performanceCyclesService.saveFrameworkSelection({
        selected_framework: selectedFramework,
      });
      setSelection(updated);
      toast.success("Framework selection saved");
    } catch {
      toast.error("Failed to save framework selection");
    }
  };

  const savePolicy = async () => {
    if (!policyDepartment.trim() || parsedFrameworks.length === 0) {
      toast.error("Department and frameworks are required");
      return;
    }

    try {
      const policy = await performanceCyclesService.upsertFrameworkPolicy({
        department: policyDepartment.trim(),
        allowed_frameworks: parsedFrameworks,
      });
      setPolicies((prev) => {
        const next = prev.filter((row) => row.department !== policy.department);
        return [policy, ...next];
      });
      toast.success("Department policy saved");
    } catch {
      toast.error("Failed to save policy");
    }
  };

  const addKpiItem = async () => {
    if (!kpiRole.trim() || !kpiTitle.trim() || !kpiDescription.trim() || !kpiMetric.trim()) {
      toast.error("Role, title, description, and KPI are required");
      return;
    }

    try {
      const item = await performanceCyclesService.createKpiLibraryItem({
        role: kpiRole.trim(),
        domain: kpiDomain.trim(),
        department: kpiDepartment.trim(),
        goal_title: kpiTitle.trim(),
        goal_description: kpiDescription.trim(),
        suggested_kpi: kpiMetric.trim(),
        suggested_weight: kpiWeight,
        framework: kpiFramework.trim() || "OKR",
      });
      setKpiItems((prev) => [item, ...prev]);
      toast.success("KPI template added");
    } catch {
      toast.error("Failed to add KPI template");
    }
  };

  const addAop = async () => {
    if (!aopObjective.trim()) {
      toast.error("Objective is required");
      return;
    }

    try {
      const item = await performanceCyclesService.createAop({
        year: aopYear,
        objective: aopObjective.trim(),
        target_value: aopTarget.trim() || undefined,
        department: aopDepartment.trim() || undefined,
      });
      setAopItems((prev) => [item, ...prev]);
      toast.success("AOP objective saved");
    } catch {
      toast.error("Failed to save AOP objective");
    }
  };

  if (!user || (user.role !== "hr" && user.role !== "leadership")) {
    return null;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Strategy Controls"
        description="Manage framework strategy, KPI templates, annual operating plans, and AI quarterly usage limits."
        action={
          <Button variant="outline" onClick={() => void initializeScreen()} disabled={loading}>
            <Sparkles className="mr-2 h-4 w-4" />
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <Card className="rounded-xl border bg-card p-4">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </Button>
          ))}
        </div>
      </Card>

      {activeTab === "framework" ? (
        <Card className="rounded-xl border bg-card p-5 space-y-4">
          <CardTitle>My Framework Selection</CardTitle>
          <CardDescription>Use recommendation guidance and save your preferred framework for upcoming cycles.</CardDescription>

          <div className="rounded-lg border border-border/70 bg-surface/60 p-4 space-y-1">
            <p className="text-sm font-medium text-foreground">Recommended: {recommendation?.recommended_framework || "-"}</p>
            <p className="text-sm text-muted-foreground">{recommendation?.rationale || "No recommendation available."}</p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto]">
            <Input value={selectedFramework} onChange={(event) => setSelectedFramework(event.target.value)} placeholder="OKR" />
            <Button onClick={saveFrameworkSelection}>Save Selection</Button>
          </div>

          {selection ? (
            <p className="text-xs text-muted-foreground">
              Current selection: {selection.selected_framework} ({selection.cycle_type})
            </p>
          ) : null}
        </Card>
      ) : null}

      {activeTab === "policies" ? (
        <Card className="rounded-xl border bg-card p-5 space-y-4">
          <CardTitle>Department Framework Policies</CardTitle>
          <CardDescription>Restrict allowed frameworks per department.</CardDescription>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <Input value={policyDepartment} onChange={(event) => setPolicyDepartment(event.target.value)} placeholder="Department" />
            <Input value={policyFrameworks} onChange={(event) => setPolicyFrameworks(event.target.value)} placeholder="OKR,MBO,Competency" />
            <Button onClick={savePolicy}>Save Policy</Button>
          </div>

          <div className="space-y-2">
            {policies.length === 0 ? (
              <p className="text-sm text-muted-foreground">No department policies configured.</p>
            ) : (
              policies.map((policy) => (
                <div key={policy.id} className="rounded-lg border border-border/70 p-3">
                  <p className="font-medium text-foreground">{policy.department}</p>
                  <p className="text-xs text-muted-foreground">Allowed: {policy.allowed_frameworks.join(", ")}</p>
                </div>
              ))
            )}
          </div>
        </Card>
      ) : null}

      {activeTab === "kpi" ? (
        <Card className="rounded-xl border bg-card p-5 space-y-4">
          <CardTitle>KPI Library</CardTitle>
          <CardDescription>Create reusable KPI templates for role-based goal generation.</CardDescription>

          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <Input value={kpiRole} onChange={(event) => setKpiRole(event.target.value)} placeholder="Role" />
            <Input value={kpiDomain} onChange={(event) => setKpiDomain(event.target.value)} placeholder="Domain (optional)" />
            <Input value={kpiDepartment} onChange={(event) => setKpiDepartment(event.target.value)} placeholder="Department (optional)" />
            <Input value={kpiFramework} onChange={(event) => setKpiFramework(event.target.value)} placeholder="Framework" />
            <Input value={kpiTitle} onChange={(event) => setKpiTitle(event.target.value)} placeholder="Goal title" />
            <Input value={String(kpiWeight)} onChange={(event) => setKpiWeight(Number(event.target.value || 0))} placeholder="Suggested weight" type="number" min={1} max={100} />
          </div>
          <Textarea value={kpiDescription} onChange={(event) => setKpiDescription(event.target.value)} placeholder="Goal description" />
          <Textarea value={kpiMetric} onChange={(event) => setKpiMetric(event.target.value)} placeholder="Suggested KPI" />
          <Button onClick={addKpiItem}>Add KPI Template</Button>

          <div className="space-y-2">
            {kpiItems.slice(0, 12).map((item) => (
              <div key={item.id} className="rounded-lg border border-border/70 p-3">
                <p className="font-medium text-foreground">{item.goal_title}</p>
                <p className="text-xs text-muted-foreground">{item.role} • {item.framework} • {item.suggested_weight}%</p>
                <p className="text-xs text-muted-foreground mt-1">KPI: {item.suggested_kpi}</p>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {activeTab === "aop" ? (
        <Card className="rounded-xl border bg-card p-5 space-y-4">
          <CardTitle>Annual Operating Plan</CardTitle>
          <CardDescription>Capture org or department objectives that influence goal generation.</CardDescription>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <Input type="number" value={String(aopYear)} onChange={(event) => setAopYear(Number(event.target.value || new Date().getFullYear()))} />
            <Input value={aopDepartment} onChange={(event) => setAopDepartment(event.target.value)} placeholder="Department (optional)" />
            <Input value={aopTarget} onChange={(event) => setAopTarget(event.target.value)} placeholder="Target value" />
          </div>
          <Textarea value={aopObjective} onChange={(event) => setAopObjective(event.target.value)} placeholder="AOP objective" />
          <Button onClick={addAop}>Save AOP Objective</Button>

          <div className="space-y-2">
            {aopItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No AOP objectives recorded.</p>
            ) : (
              aopItems.slice(0, 12).map((item) => (
                <div key={item.id} className="rounded-lg border border-border/70 p-3">
                  <p className="font-medium text-foreground">{item.year} • {item.department || "Organization"}</p>
                  <p className="text-sm text-muted-foreground">{item.objective}</p>
                  {item.target_value ? <p className="text-xs text-muted-foreground">Target: {item.target_value}</p> : null}
                </div>
              ))
            )}
          </div>
        </Card>
      ) : null}

      {activeTab === "ai-usage" ? (
        <Card className="rounded-xl border bg-card p-5 space-y-4">
          <CardTitle>AI Quarterly Usage</CardTitle>
          <CardDescription>
            Current cycle: Q{usage?.quarter || "-"} {usage?.year || "-"}
          </CardDescription>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {(usage?.features || []).map((feature) => (
              <div key={feature.feature_name} className="rounded-lg border border-border/70 p-3 space-y-2">
                <p className="text-sm font-medium text-foreground">{feature.feature_name.replaceAll("_", " ")}</p>
                <p className="text-xs text-muted-foreground">Used {feature.used} / {feature.limit}</p>
                <div className="h-2 w-full rounded bg-muted/70">
                  <div
                    className="h-2 rounded bg-primary"
                    style={{ width: `${Math.min((feature.used / Math.max(feature.limit, 1)) * 100, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Remaining: {feature.remaining}</p>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </motion.div>
  );
}

