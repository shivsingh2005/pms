"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { AdminDashboard } from "@/components/dashboard/AdminDashboard";
import { useSessionStore } from "@/store/useSessionStore";

export default function AdminDashboardPage() {
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
        title="Admin Dashboard"
        description="System control center for user governance, role assignment, and settings."
      />
      <AdminDashboard />
    </motion.div>
  );
}
