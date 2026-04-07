"use client";

import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { ConsolidatedCheckinForm } from "@/components/checkins/ConsolidatedCheckinForm";

export default function CheckinsPage() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-7">
      <PageHeader
        title="Check-ins"
        description="Submit one unified employee check-in that covers all assigned goals for the current cycle."
      />
      <ConsolidatedCheckinForm />
    </motion.div>
  );
}

