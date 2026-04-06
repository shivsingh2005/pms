"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { EmployeeDashboard } from "@/components/dashboard/EmployeeDashboard";
import { WhatsNextBanner } from "@/components/dashboard/WhatsNextBanner";
import { useSessionStore } from "@/store/useSessionStore";

export default function EmployeeDashboardPage() {
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
        title="Employee Dashboard"
        description="Snapshot of your progress with one clear next step. Use Growth Hub and Goals for deeper analysis."
      />
      <WhatsNextBanner />
      <EmployeeDashboard />
    </motion.div>
  );
}

