"use client";

import dynamic from "next/dynamic";
import { Toaster } from "sonner";
import { useAuthBootstrap } from "@/hooks/useAuthBootstrap";
import { useSessionStore } from "@/store/useSessionStore";

const AIChatWidget = dynamic(
  () => import("@/components/ai/AIChatWidget").then((mod) => mod.AIChatWidget),
  { ssr: false },
);

export function AppProviders({ children }: { children: React.ReactNode }) {
  useAuthBootstrap();
  const user = useSessionStore((state) => state.user);
  const isAuthLoading = useSessionStore((state) => state.isAuthLoading);

  if (isAuthLoading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      {children}
      {user && <AIChatWidget />}
      <Toaster richColors position="top-right" />
    </>
  );
}
