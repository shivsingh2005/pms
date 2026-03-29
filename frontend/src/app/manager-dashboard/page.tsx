"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { ManagerDashboard } from "@/components/dashboard/ManagerDashboard";
import { useSessionStore } from "@/store/useSessionStore";

export default function ManagerDashboardPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);
  const activeMode = useSessionStore((state) => state.activeMode);
  const setActiveMode = useSessionStore((state) => state.setActiveMode);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    if (activeMode !== "manager") {
      setActiveMode("manager");
    }
  }, [activeMode, router, setActiveMode, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader
        title="Manager Dashboard"
        description="Team management center for overview, allotments, approvals, performance, meetings, and AI insights."
      />
      <ManagerDashboard />
    </motion.div>
  );
}
