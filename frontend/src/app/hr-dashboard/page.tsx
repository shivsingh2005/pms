"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { HRDashboard } from "@/components/dashboard/HRDashboard";
import { useSessionStore } from "@/store/useSessionStore";

export default function HRDashboardPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  useEffect(() => {
    if (!user) {
      router.push("/");
    }
  }, [router, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="HR Dashboard"
        description="Organization monitoring center for directory, analytics, calibration, reporting, and risk analysis."
      />
      <HRDashboard />
    </motion.div>
  );
}
