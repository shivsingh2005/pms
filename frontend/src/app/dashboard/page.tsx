"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LayoutDashboard } from "lucide-react";
import { RoleDashboard } from "@/components/dashboard/RoleDashboard";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { useSessionStore } from "@/store/useSessionStore";

export default function DashboardPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);

  useEffect(() => {
    if (!user) router.push("/");
  }, [router, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title={`${user.role.toUpperCase()} Dashboard`}
        description="Guided workflow for goals, check-ins, reviews, and AI insights."
        action={
          <Link href="/goals">
            <Button>Create Goal</Button>
          </Link>
        }
      />
      <Card className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <LayoutDashboard className="h-3.5 w-3.5" /> Workspace Overview
        </div>
        <CardTitle>Performance Snapshot</CardTitle>
        <CardDescription>Track progress signals, trends, and team outcomes in one place.</CardDescription>
      </Card>
      <RoleDashboard role={user.role} />
    </motion.div>
  );
}
