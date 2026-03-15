"use client";

import { Toaster } from "sonner";
import { useAuthBootstrap } from "@/hooks/useAuthBootstrap";
import { AIChatWidget } from "@/components/ai/AIChatWidget";
import { useSessionStore } from "@/store/useSessionStore";

export function AppProviders({ children }: { children: React.ReactNode }) {
  useAuthBootstrap();
  const user = useSessionStore((state) => state.user);

  return (
    <>
      {children}
      {user && <AIChatWidget />}
      <Toaster richColors position="top-right" />
    </>
  );
}
