"use client";

import { useEffect } from "react";
import { authCookies } from "@/lib/cookies";
import { authService } from "@/services/auth";
import { useSessionStore } from "@/store/useSessionStore";

export function useAuthBootstrap() {
  const setUser = useSessionStore((state) => state.setUser);

  useEffect(() => {
    const token = authCookies.getToken();
    if (!token) {
      setUser(null);
      return;
    }

    authService
      .me()
      .then((user) => setUser(user))
      .catch(() => {
        authCookies.clearToken();
        setUser(null);
      });
  }, [setUser]);
}
