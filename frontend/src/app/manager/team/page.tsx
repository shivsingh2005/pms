import dynamic from "next/dynamic";
import { Suspense } from "react";
import { DashboardSkeleton } from "@/components/skeletons/DashboardSkeleton";

const PageView = dynamic(() => import("@/app/manager/team-dashboard/page"), { ssr: false });

export default function Page() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <PageView />
    </Suspense>
  );
}