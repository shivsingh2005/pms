"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardError } from "@/components/ui/DashboardError";
import { useAuth } from "@/context/AuthContext";
import { WhatsNextBanner } from "@/components/dashboard/WhatsNextBanner";
import { LeadershipDashboard } from "@/components/dashboard/LeadershipDashboard";

export default function LeadershipOrgDashboardPage() {
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

    if (user.role !== "leadership" && user.role !== "hr") {
      router.push("/unauthorized");
    }
  }, [ready, router, user]);

  if (!ready) {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  if (!user || (user.role !== "leadership" && user.role !== "hr")) {
    return <Skeleton className="h-[460px] rounded-2xl" />;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Leadership Dashboard"
        description="Executive snapshot with one priority action. Open trend and talent pages for deeper analysis."
      />
      <DashboardError name="LeadershipDashboard">
        <WhatsNextBanner />
        <LeadershipDashboard />
      </DashboardError>
    </motion.div>
  );
}

