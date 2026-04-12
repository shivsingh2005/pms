"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardError } from "@/components/ui/DashboardError";
import { WhatsNextBanner } from "@/components/dashboard/WhatsNextBanner";
import { EmployeeDashboard } from "@/components/dashboard/EmployeeDashboard";
import { useAuth } from "@/context/AuthContext";

export default function EmployeeDashboardPage() {
  const router = useRouter();
  const { user, ready } = useAuth();

  useEffect(() => {
    if (!ready) {
      return;
    }

    if (!user) {
      router.push("/");
      return;
    }

    if (user.role !== "employee") {
      router.push("/unauthorized");
      return;
    }
  }, [ready, router, user]);

  if (!ready) {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  if (!user || user.role !== "employee") {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Employee Dashboard"
        description="Snapshot of your progress with one clear next step. Use Growth Hub and Goals for deeper analysis."
      />
      <DashboardError name="EmployeeDashboard">
        <WhatsNextBanner />
        <EmployeeDashboard />
      </DashboardError>
    </motion.div>
  );
}

