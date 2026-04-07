"use client";

import { useEffect } from "react";
import { authCookies } from "@/lib/cookies";
import { authService } from "@/services/auth";
import { useSessionStore } from "@/store/useSessionStore";

export function useAuthBootstrap() {
  const setUser = useSessionStore((state) => state.setUser);
  const setAuthLoading = useSessionStore((state) => state.setAuthLoading);

  useEffect(() => {
    setAuthLoading(true);

    const token = authCookies.getToken();
    if (!token) {
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          setUser(parsed);
          localStorage.setItem(
            "session",
            JSON.stringify({ userId: parsed.id, email: parsed.email, role: parsed.role }),
          );
        } catch {
          setUser(null);
          localStorage.removeItem("user");
          localStorage.removeItem("session");
        }
      } else {
        setUser(null);
      }
      setAuthLoading(false);
      return;
    }

    authService
      .me()
      .then((user) => {
        setUser(user);
        localStorage.setItem("user", JSON.stringify(user));
        localStorage.setItem("session", JSON.stringify({ userId: user.id, email: user.email, role: user.role }));
      })
      .catch(() => {
        authCookies.clearToken();
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("session");
      })
      .finally(() => {
        setAuthLoading(false);
      });
  }, [setAuthLoading, setUser]);
}
