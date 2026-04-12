"use client";

import dynamic from "next/dynamic";
import { Toaster } from "sonner";
import { useAuthBootstrap } from "@/hooks/useAuthBootstrap";
import { useSessionStore } from "@/store/useSessionStore";
import { AuthProvider } from "@/context/AuthContext";
import { QueryProvider } from "@/components/providers/query-provider";

const AIChatWidget = dynamic(
  () => import("@/components/ai/AIChatWidget").then((mod) => mod.AIChatWidget),
  { ssr: false },
);

export function AppProviders({ children }: { children: React.ReactNode }) {
  useAuthBootstrap();
  const user = useSessionStore((state) => state.user);

  return (
    <AuthProvider>
      <QueryProvider>
        {children}
        {user && <AIChatWidget />}
        <Toaster richColors position="top-right" />
      </QueryProvider>
    </AuthProvider>
  );
}
