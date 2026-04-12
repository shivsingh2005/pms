"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardError } from "@/components/ui/DashboardError";
import { useAuth } from "@/context/AuthContext";
import { WhatsNextBanner } from "@/components/dashboard/WhatsNextBanner";
import { ManagerDashboard } from "@/components/dashboard/ManagerDashboard";

export default function ManagerDashboardPage() {
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

    if (user.role !== "manager") {
      router.push("/unauthorized");
      return;
    }
  }, [ready, router, user]);

  if (!ready) {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  if (!user || user.role !== "manager") {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Manager Dashboard"
        description="Snapshot view for team health and immediate approvals. Open Team Performance for deep analytics."
      />
      <DashboardError name="ManagerDashboard">
        <WhatsNextBanner />
        <ManagerDashboard />
      </DashboardError>
    </motion.div>
  );
}

