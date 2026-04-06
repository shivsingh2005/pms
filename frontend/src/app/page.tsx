"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { authService } from "@/services/auth";
import { authCookies } from "@/lib/cookies";
import { useSessionStore } from "@/store/useSessionStore";
import { resolveDefaultRouteForRole } from "@/lib/role-access";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function normalizeLoginEmail(email: string): string | null {
  const trimmed = email.trim().toLowerCase();
  if (!trimmed) {
    return null;
  }

  return trimmed;
}

export default function HomePage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const user = useSessionStore((state) => state.user);
  const setUser = useSessionStore((state) => state.setUser);
  const logout = useSessionStore((state) => state.logout);

  useEffect(() => {
    if (!user) {
      return;
    }

    router.replace(resolveDefaultRouteForRole(user.role));
  }, [router, user]);

  return (
    <div className="relative grid min-h-[78vh] place-items-center overflow-hidden">
      <div className="pointer-events-none absolute -top-32 left-0 h-72 w-72 rounded-full bg-primary/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-10 top-10 h-72 w-72 rounded-full bg-secondary/15 blur-3xl" />
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="space-y-5 rounded-2xl border border-border/75 bg-card/95 p-7 shadow-elevated">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" /> Intelligent Performance Workspace
            </div>
            <CardTitle className="text-3xl font-semibold">AI-native PMS</CardTitle>
            <CardDescription>Modern performance management with goals, check-ins, reviews, and AI guidance.</CardDescription>
          </div>

          <label className="text-sm font-medium text-foreground">Email</label>
          <Input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            type="email"
          />

          <div className="pt-1">
            <Button
              className="w-full"
              disabled={loading || !email.trim()}
              onClick={async () => {
                setLoading(true);
                try {
                  const normalizedEmail = normalizeLoginEmail(email);
                  if (!normalizedEmail) {
                    return;
                  }

                  const token = await authService.login({ email: normalizedEmail });

                  // Reset in-memory session state before applying the new login response.
                  logout();
                  authCookies.clearToken();
                  authCookies.clearRefreshToken();

                  authCookies.setToken(token.access_token);
                  authCookies.setRefreshToken(token.refresh_token);

                  const me = await authService.me();
                  setUser(me);
                  localStorage.setItem("user", JSON.stringify(me));
                  localStorage.setItem(
                    "session",
                    JSON.stringify({
                      userId: me.id,
                      email: me.email,
                      role: me.role,
                    }),
                  );
                  toast.success(`Welcome back, ${me.name}`);

                  // Smooth OAuth onboarding: if Google is not connected yet, start OAuth right after app sign-in.
                  try {
                    const google = await authService.getGoogleConnectionStatus();
                    if (!google.connected) {
                      const { authorization_url } = await authService.getGoogleAuthorizeUrl();
                      if (authorization_url) {
                        window.location.href = authorization_url;
                        return;
                      }
                    }
                  } catch {
                    // If Google OAuth cannot be initialized, continue with app sign-in session.
                  }

                  const targetRoute = resolveDefaultRouteForRole(me.role);
                  router.replace(targetRoute);
                } finally {
                  setLoading(false);
                }
              }}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}

