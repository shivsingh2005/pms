import dynamic from "next/dynamic";
import { Suspense } from "react";
import { DashboardSkeleton } from "@/components/skeletons/DashboardSkeleton";

const PageView = dynamic(() => import("@/components/dashboards/hr/HRDashboard"), { ssr: false });

export default function Page() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <PageView />
    </Suspense>
  );
}