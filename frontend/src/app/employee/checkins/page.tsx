import dynamic from "next/dynamic";
import { Suspense } from "react";
import { DashboardSkeleton } from "@/components/skeletons/DashboardSkeleton";

const PageView = dynamic(() => import("@/app/checkins/page"), { ssr: false });

export default function Page() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <PageView />
    </Suspense>
  );
}