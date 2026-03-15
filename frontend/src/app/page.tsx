"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { authService } from "@/services/auth";
import { authCookies } from "@/lib/cookies";
import { useSessionStore } from "@/store/useSessionStore";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const roles = ["employee", "manager", "hr", "leadership", "admin"] as const;

export default function HomePage() {
  const router = useRouter();
  const [role, setRole] = useState<(typeof roles)[number]>("employee");
  const [email, setEmail] = useState("employee@example.com");
  const [name, setName] = useState("Demo User");
  const [loading, setLoading] = useState(false);
  const setUser = useSessionStore((state) => state.setUser);

  return (
    <div className="grid min-h-[72vh] place-items-center">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="space-y-5">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" /> Intelligent Performance Workspace
            </div>
            <CardTitle className="text-3xl font-semibold">AI-native PMS</CardTitle>
            <CardDescription>Modern performance management with goals, check-ins, reviews, and AI guidance.</CardDescription>
          </div>

          <label className="text-sm font-medium text-foreground">Role</label>
          <select
            className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground focus:border-primary/55 focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={role}
            onChange={(e) => setRole(e.target.value as (typeof roles)[number])}
          >
            {roles.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <label className="text-sm font-medium text-foreground">Email</label>
          <Input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            type="email"
          />

          <label className="text-sm font-medium text-foreground">Name</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />

          <div className="pt-1">
            <Button
              className="w-full"
              disabled={loading || !email.trim() || !name.trim()}
              onClick={async () => {
                setLoading(true);
                try {
                  const token = await authService.roleLogin({ role, email: email.trim(), name: name.trim() });
                  authCookies.setToken(token.access_token);
                  authCookies.setRefreshToken(token.refresh_token);
                  const me = await authService.me();
                  setUser(me);
                  router.push("/dashboard");
                } finally {
                  setLoading(false);
                }
              }}
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
