"use client";

import { useEffect } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LayoutDashboard } from "lucide-react";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import { useSessionStore } from "@/store/useSessionStore";

const RoleDashboard = dynamic(
  () => import("@/components/dashboard/RoleDashboard").then((mod) => mod.RoleDashboard),
  {
    loading: () => <Skeleton className="h-[22rem] w-full" />,
  },
);

export default function DashboardPage() {
  const router = useRouter();
  const user = useSessionStore((s) => s.user);

  useEffect(() => {
    if (!user) router.push("/");
  }, [router, user]);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mx-auto w-full max-w-7xl space-y-6 px-6 py-6">
      <PageHeader
        title={`${user.role.toUpperCase()} Dashboard`}
        description="Guided workflow for goals, check-ins, reviews, and AI insights."
        action={
          <Link href="/goals">
            <Button>Create Goal</Button>
          </Link>
        }
      />
      <SectionWrapper>
        <SectionContainer>
          <Card className="space-y-3 rounded-2xl border border-border/75 bg-card/90 p-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <LayoutDashboard className="h-3.5 w-3.5" /> Workspace Overview
            </div>
            <CardTitle>Performance Snapshot</CardTitle>
            <CardDescription>
              Track progress signals, trends, and team outcomes in one place with a clean operational view.
            </CardDescription>
          </Card>
        </SectionContainer>
        <RoleDashboard role={user.role} />
      </SectionWrapper>
    </motion.div>
  );
}
