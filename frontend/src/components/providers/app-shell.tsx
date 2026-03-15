"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  CalendarCheck,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Sparkles,
  Sun,
  Target,
  Video,
  X,
} from "lucide-react";
import { motion } from "framer-motion";
import { authCookies } from "@/lib/cookies";
import { useSessionStore } from "@/store/useSessionStore";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/checkins", label: "Check-ins", icon: CalendarCheck },
  { href: "/meetings", label: "Meetings", icon: Video },
  { href: "/reviews", label: "Reviews", icon: ClipboardList },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [dark, setDark] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const user = useSessionStore((s) => s.user);
  const logout = useSessionStore((s) => s.logout);
  const withAppShell = Boolean(user);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("pms-theme") : null;
    const isDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", isDark);
    setDark(isDark);
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("pms-theme", next ? "dark" : "light");
  };

  const handleLogout = () => {
    authCookies.clearToken();
    authCookies.clearRefreshToken();
    logout();
    setUserMenuOpen(false);
    setMobileNavOpen(false);
    router.push("/");
  };

  useEffect(() => {
    const onClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    setMobileNavOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  const initials =
    user?.name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((item) => item[0]?.toUpperCase())
      .join("") ?? "U";

  const sidebarLinks = (
    <div className="space-y-1.5 px-3">
      {nav.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{item.label}</span>
            {active && <motion.div layoutId="nav-highlight" className="absolute inset-0 rounded-lg border border-primary/40" />}
          </Link>
        );
      })}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      {withAppShell && (
        <>
          <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 border-r bg-card lg:flex lg:flex-col">
            <div className="flex h-16 items-center border-b px-4">
              <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="rounded-lg bg-primary/10 p-1.5 text-primary">
                  <Sparkles className="h-4 w-4" />
                </span>
                AI PMS
              </Link>
            </div>
            <div className="flex-1 py-4">{sidebarLinks}</div>
            <div className="border-t p-4">
              <div className="rounded-lg bg-muted/60 p-3">
                <p className="truncate text-sm font-medium text-foreground">{user?.name}</p>
                <p className="truncate text-xs uppercase tracking-wide text-muted-foreground">{user?.role}</p>
              </div>
            </div>
          </aside>

          {mobileNavOpen && (
            <div className="fixed inset-0 z-50 lg:hidden">
              <button
                type="button"
                className="absolute inset-0 bg-background/70 backdrop-blur-sm"
                onClick={() => setMobileNavOpen(false)}
                aria-label="Close mobile menu"
              />
              <aside className="relative z-10 flex h-full w-60 flex-col border-r bg-card">
                <div className="flex h-16 items-center justify-between border-b px-4">
                  <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                    <span className="rounded-lg bg-primary/10 p-1.5 text-primary">
                      <Sparkles className="h-4 w-4" />
                    </span>
                    AI PMS
                  </Link>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setMobileNavOpen(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex-1 py-4">{sidebarLinks}</div>
              </aside>
            </div>
          )}

          <header className="fixed inset-x-0 top-0 z-30 h-16 border-b bg-card/95 backdrop-blur lg:left-60">
            <div className="flex h-full items-center justify-between gap-4 px-4 sm:px-6">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <Button variant="ghost" size="sm" className="h-9 w-9 p-0 lg:hidden" onClick={() => setMobileNavOpen(true)}>
                  <Menu className="h-4 w-4" />
                </Button>
                <div className="max-w-md flex-1">
                  <Input placeholder="Search..." className="h-9 bg-background" />
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <Button variant="ghost" size="sm" className="h-9 w-9 rounded-full p-0" aria-label="Notifications">
                  <Bell className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={toggleTheme} className="h-9 w-9 rounded-full p-0">
                  {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </Button>
                <div className="relative" ref={userMenuRef}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-9 rounded-full px-1.5"
                    onClick={() => setUserMenuOpen((prev) => !prev)}
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                      {initials}
                    </span>
                  </Button>
                  {userMenuOpen && (
                    <div className="absolute right-0 top-11 w-52 rounded-xl border bg-card p-2 shadow-sm">
                      <div className="px-2 py-2">
                        <p className="truncate text-sm font-medium text-foreground">{user?.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
                      </div>
                      <Button variant="ghost" size="sm" className="w-full justify-start gap-2" onClick={handleLogout}>
                        <LogOut className="h-4 w-4" />
                        Logout
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </header>
        </>
      )}

      <main className={cn("min-h-screen", withAppShell ? "pt-16 lg:pl-60" : "")}> 
        <div className={cn(withAppShell ? "h-[calc(100vh-4rem)] overflow-y-auto" : "")}> 
          <div className="mx-auto w-full max-w-7xl px-6 py-6">{children}</div>
        </div>
      </main>
    </div>
  );
}
