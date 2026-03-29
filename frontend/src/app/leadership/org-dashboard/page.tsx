"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { LeadershipDashboard } from "@/components/dashboard/LeadershipDashboard";
import { useSessionStore } from "@/store/useSessionStore";

export default function LeadershipOrgDashboardPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  if (!user) {
    return null;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Leadership Dashboard"
        description="Strategic insights center for organizational trends, talent, attrition, and business KPIs."
      />
      <LeadershipDashboard />
    </motion.div>
  );
}
