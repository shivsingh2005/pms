"use client";

import { useEffect } from "react";
import { authCookies } from "@/lib/cookies";
import { authService } from "@/services/auth";
import { useSessionStore } from "@/store/useSessionStore";

export function useAuthBootstrap() {
  const setUser = useSessionStore((state) => state.setUser);
  const setAuthLoading = useSessionStore((state) => state.setAuthLoading);

  useEffect(() => {
    let cancelled = false;

    const initAuth = async () => {
      try {
        setAuthLoading(true);

        const token = authCookies.getToken();
        if (!token) {
          const storedUser = localStorage.getItem("user");
          if (storedUser) {
            try {
              const parsed = JSON.parse(storedUser);
              if (!cancelled) {
                setUser(parsed);
                localStorage.setItem(
                  "session",
                  JSON.stringify({ userId: parsed.id, email: parsed.email, role: parsed.role }),
                );
              }
            } catch {
              if (!cancelled) {
                setUser(null);
                localStorage.removeItem("user");
                localStorage.removeItem("session");
              }
            }
          } else {
            if (!cancelled) {
              setUser(null);
            }
          }
          if (!cancelled) {
            setAuthLoading(false);
          }
          return;
        }

        try {
          const user = await authService.me();
          if (!cancelled) {
            setUser(user);
            localStorage.setItem("user", JSON.stringify(user));
            localStorage.setItem("session", JSON.stringify({ userId: user.id, email: user.email, role: user.role }));
          }
        } catch {
          if (!cancelled) {
            authCookies.clearToken();
            setUser(null);
            localStorage.removeItem("user");
            localStorage.removeItem("session");
          }
        } finally {
          if (!cancelled) {
            setAuthLoading(false);
          }
        }
      } catch (error) {
        console.error("Auth bootstrap error:", error);
        if (!cancelled) {
          setAuthLoading(false);
          setUser(null);
        }
      }
    };

    initAuth();

    return () => {
      cancelled = true;
    };
  }, [setAuthLoading, setUser]);
}
