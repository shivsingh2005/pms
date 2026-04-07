"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionStore } from "@/store/useSessionStore";
import { resolveDefaultRouteForRole } from "@/lib/role-access";

export default function DashboardPage() {
  const router = useRouter();
  const user = useSessionStore((state) => state.user);

  useEffect(() => {
    if (!user) {
      router.push("/");
      return;
    }

    router.replace(resolveDefaultRouteForRole(user.role));
  }, [router, user]);

  return null;
}
