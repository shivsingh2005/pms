"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  LogOut,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { authCookies } from "@/lib/cookies";
import { useSessionStore } from "@/store/useSessionStore";
import type { UserRole } from "@/types";
import { cn } from "@/lib/utils";
import { EmployeeSidebar } from "@/components/navigation/EmployeeSidebar";
import { ManagerSidebar } from "@/components/navigation/ManagerSidebar";
import { HRSidebar } from "@/components/navigation/HRSidebar";
import { LeadershipSidebar } from "@/components/navigation/LeadershipSidebar";
import { AdminSidebar } from "@/components/navigation/AdminSidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { isAuthFreePath, isPathAllowedForRole, resolveDefaultRouteForRole } from "@/lib/role-access";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [dark, setDark] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const setActiveMode = useSessionStore((s) => s.setActiveMode);
  const logout = useSessionStore((s) => s.logout);
  const withAppShell = Boolean(user);
  const hasManagerRole = user?.role === "manager";

  const canSwitchMode = hasManagerRole;
  const effectiveRole: UserRole | null = user
    ? (hasManagerRole ? activeMode ?? "manager" : user.role)
    : null;
  const homeHref = effectiveRole ? resolveDefaultRouteForRole(effectiveRole) : "/";

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("pms-theme") : null;
    const isDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", isDark);
    setDark(isDark);

    const collapsed = typeof window !== "undefined" ? localStorage.getItem("pms-sidebar-collapsed") : null;
    setSidebarCollapsed(collapsed === "true");
  }, []);

  useEffect(() => {
    if (hasManagerRole && !activeMode) {
      setActiveMode("manager");
    }
  }, [activeMode, hasManagerRole, setActiveMode]);

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

  const toggleSidebar = () => {
    const next = !sidebarCollapsed;
    setSidebarCollapsed(next);
    localStorage.setItem("pms-sidebar-collapsed", next ? "true" : "false");
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

  useEffect(() => {
    if (!user || !effectiveRole) {
      return;
    }

    if (!isPathAllowedForRole(pathname, effectiveRole)) {
      router.replace(resolveDefaultRouteForRole(effectiveRole));
    }
  }, [effectiveRole, pathname, router, user]);

  useEffect(() => {
    if (!user && !isAuthFreePath(pathname)) {
      router.replace("/");
    }
  }, [pathname, router, user]);

  const initials =
    user?.name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((item) => item[0]?.toUpperCase())
      .join("") ?? "U";

  const sidebarLinks =
    effectiveRole === "employee" ? (
      <EmployeeSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    ) : effectiveRole === "manager" ? (
      <ManagerSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    ) : effectiveRole === "hr" ? (
      <HRSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    ) : effectiveRole === "leadership" ? (
      <LeadershipSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    ) : (
      <AdminSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    );

  return (
    <div className="min-h-screen bg-background text-foreground">
      {withAppShell && (
        <>
          <aside className={cn("fixed inset-y-0 left-0 z-40 hidden border-r border-gray-200 bg-card/95 backdrop-blur transition-all duration-200 dark:border-gray-800 lg:flex lg:flex-col", sidebarCollapsed ? "w-20" : "w-64")}>
            <div className={cn("flex h-16 items-center border-b border-border/70", sidebarCollapsed ? "justify-center px-2" : "px-5")}>
              <Link href={homeHref} className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="rounded-xl border border-primary/20 bg-primary/15 p-1.5 text-primary shadow-card">
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                </span>
                {!sidebarCollapsed ? "AI Native PMS" : null}
              </Link>
            </div>
            <div className="flex-1 py-5">{sidebarLinks}</div>
            <div className="border-t border-border/70 p-4">
              {sidebarCollapsed ? (
                <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">{initials}</div>
              ) : (
                <div className="rounded-xl border border-border/70 bg-surface/65 p-3">
                  <p className="truncate text-sm font-medium text-foreground">{user?.name}</p>
                  <p className="truncate text-xs uppercase tracking-wide text-muted-foreground">{effectiveRole ?? user?.role}</p>
                </div>
              )}
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
              <aside className="relative z-10 flex h-full w-64 flex-col border-r border-gray-200 bg-card dark:border-gray-800">
                <div className="flex h-16 items-center justify-between border-b border-border/70 px-4">
                  <Link href={homeHref} className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                    <span className="rounded-xl border border-primary/20 bg-primary/15 p-1.5 text-primary">
                      <Sparkles className="h-4 w-4" />
                    </span>
                    AI Native PMS
                  </Link>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setMobileNavOpen(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex-1 py-4">{sidebarLinks}</div>
              </aside>
            </div>
          )}

          <header className={cn("fixed inset-x-0 top-0 z-30 h-16 border-b border-border/70 bg-card/85 backdrop-blur-lg transition-all duration-200", sidebarCollapsed ? "lg:left-20" : "lg:left-64")}>
            <div className="flex h-full items-center justify-between gap-4 px-4 sm:px-8">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <Button variant="ghost" size="sm" className="h-9 w-9 p-0 lg:hidden" onClick={() => setMobileNavOpen(true)}>
                  <Menu className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="hidden h-9 w-9 p-0 lg:inline-flex" onClick={toggleSidebar} aria-label="Toggle sidebar">
                  {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                </Button>
                <div className="relative max-w-md flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input placeholder="Search goals, check-ins, reviews..." className="h-10 rounded-xl bg-background pl-9" />
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                {canSwitchMode && effectiveRole && (
                  <div className="hidden items-center gap-2 md:flex">
                    <span className="text-xs text-muted-foreground">Switch View</span>
                    <select
                      className="h-9 rounded-md border border-input bg-card px-2 text-sm text-foreground"
                      value={effectiveRole}
                      onChange={(event) => {
                        const mode = event.target.value as "employee" | "manager";
                        setActiveMode(mode);
                        router.push(mode === "manager" ? "/manager/dashboard" : "/employee/dashboard");
                      }}
                    >
                      <option value="manager">Manager Mode</option>
                      <option value="employee">Employee Mode</option>
                    </select>
                  </div>
                )}
                <Button variant="ghost" size="sm" className="h-9 w-9 rounded-full p-0" aria-label="Notifications">
                  <Bell className="h-4 w-4" />
                </Button>
                <Button variant="secondary" size="sm" onClick={toggleTheme} className="h-9 w-9 rounded-full p-0" aria-label="Toggle theme">
                  {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </Button>
                <div className="dashboard-dropdown-root" ref={userMenuRef}>
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
                    <div className="absolute right-0 top-11 z-[9999] w-56 rounded-2xl border border-border/80 bg-card p-2.5 shadow-floating">
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

      <main className={cn("min-h-screen", withAppShell ? (sidebarCollapsed ? "pt-16 lg:pl-20" : "pt-16 lg:pl-64") : "") }>
        <div className={cn(withAppShell ? "h-[calc(100vh-4rem)] overflow-y-auto" : "")}>
          <div className="mx-auto w-full max-w-7xl px-6 py-6 space-y-3">
            {canSwitchMode && effectiveRole && (
              <div className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                Viewing as {effectiveRole === "manager" ? "Manager" : "Employee"}
              </div>
            )}
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
