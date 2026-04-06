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
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { authCookies } from "@/lib/cookies";
import { useSessionStore } from "@/store/useSessionStore";
import type { UserRole } from "@/types";
import type { NotificationItem } from "@/types";
import type { NotificationsPayload } from "@/types";
import { cn } from "@/lib/utils";
import { EmployeeSidebar } from "@/components/navigation/EmployeeSidebar";
import { ManagerSidebar } from "@/components/navigation/ManagerSidebar";
import { HRSidebar } from "@/components/navigation/HRSidebar";
import { LeadershipSidebar } from "@/components/navigation/LeadershipSidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { isAuthFreePath, isPathAllowedForRole, resolveDefaultRouteForRole } from "@/lib/role-access";
import { authService } from "@/services/auth";
import { notificationsService } from "@/services/notifications";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [dark, setDark] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [tourOpen, setTourOpen] = useState(false);
  const [tourStep, setTourStep] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const user = useSessionStore((s) => s.user);
  const activeMode = useSessionStore((s) => s.activeMode);
  const setActiveMode = useSessionStore((s) => s.setActiveMode);
  const patchUser = useSessionStore((s) => s.patchUser);
  const logout = useSessionStore((s) => s.logout);
  const withAppShell = Boolean(user);
  const hasManagerRole = user?.role === "manager";
  const canSwitchMode = hasManagerRole;
  const effectiveRole: UserRole | null = user
    ? (hasManagerRole ? activeMode ?? "manager" : user.role)
    : null;
  const homeHref = effectiveRole ? resolveDefaultRouteForRole(effectiveRole) : "/";

  const tourStepsByRole: Record<UserRole, string[]> = {
    employee: [
      "Welcome! I am your PMS Buddy and I will guide your cycle.",
      "Set role-aligned goals with AI suggestions.",
      "Submit check-ins after goals are approved.",
      "Meetings are auto-proposed from check-ins.",
      "Track growth and progress from your dashboard.",
      "You are all set. I will keep showing next actions.",
    ],
    manager: [
      "Welcome manager. Review your team queue first.",
      "Approve or edit goals to unlock check-ins.",
      "Review check-ins and meeting outcomes.",
      "Submit ratings with coaching feedback.",
      "Use team performance and stack ranking for decisions.",
      "You are all set to coach your team effectively.",
    ],
    hr: [
      "Welcome HR. You control cycle health and calibration.",
      "Monitor analytics and training needs.",
      "Use calibration and 9-box to identify talent priorities.",
      "Generate reports and guide managers with interventions.",
      "Track succession readiness from strategic signals.",
      "You are all set with full organization visibility.",
    ],
    leadership: [
      "Welcome leadership. Track organization talent signals.",
      "Use dashboards for trend-led decision making.",
      "Inspect business-unit performance and risk clusters.",
      "Use calibration summaries and succession insights.",
      "Review intervention recommendations from AI.",
      "You are all set for confident talent decisions.",
    ],
  };

  useEffect(() => {
    if (hasManagerRole && !activeMode) {
      setActiveMode("manager");
    }
  }, [activeMode, hasManagerRole, setActiveMode]);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("pms-theme") : null;
    const isDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", isDark);
    setDark(isDark);

    const collapsed = typeof window !== "undefined" ? localStorage.getItem("pms-sidebar-collapsed") : null;
    setSidebarCollapsed(collapsed === "true");
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
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };

    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    let cancelled = false;

    const load = async () => {
      const payload = (await notificationsService.list().catch(() => null)) as NotificationsPayload | null;
      if (!payload || cancelled) {
        return;
      }
      setNotifications(payload.items);
      setUnreadCount(payload.unread_count);
    };

    load().catch(() => null);
    const timer = window.setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      load().catch(() => null);
    }, 120000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [user]);

  useEffect(() => {
    if (!user) {
      setTourOpen(false);
      setTourStep(0);
      return;
    }

    const shouldShowTour = Boolean(user.first_login || !user.onboarding_complete);
    if (shouldShowTour) {
      setTourOpen(true);
      setTourStep(0);
    }
  }, [user]);

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
    ) : (
      <LeadershipSidebar pathname={pathname} collapsed={sidebarCollapsed} />
    );

  return (
    <div className="min-h-screen bg-background text-foreground">
      {withAppShell && (
        <>
          <aside className={cn("fixed inset-y-0 left-0 z-40 hidden border-r border-border bg-card transition-all duration-200 lg:flex lg:flex-col", sidebarCollapsed ? "w-20" : "w-64")}>
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
                  {canSwitchMode ? (
                    <div className="mt-2 flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 p-1 text-xs">
                      <button
                        type="button"
                        onClick={() => {
                          setActiveMode("employee");
                          router.push("/employee/dashboard");
                        }}
                        className={cn(
                          "rounded-full px-2 py-1",
                          effectiveRole === "employee" ? "bg-primary text-primary-foreground" : "text-primary"
                        )}
                      >
                        Employee
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveMode("manager");
                          router.push("/manager/dashboard");
                        }}
                        className={cn(
                          "rounded-full px-2 py-1",
                          effectiveRole === "manager" ? "bg-primary text-primary-foreground" : "text-primary"
                        )}
                      >
                        Manager
                      </button>
                    </div>
                  ) : null}
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
              <aside className="relative z-10 flex h-full w-64 flex-col border-r border-border bg-card">
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

          <header className={cn("fixed inset-x-0 top-0 z-30 h-16 border-b border-border bg-card transition-all duration-200", sidebarCollapsed ? "lg:left-20" : "lg:left-64")}>
            <div className="flex h-full items-center justify-between gap-4 px-4 sm:px-8">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <Button variant="ghost" size="sm" className="h-9 w-9 p-0 lg:hidden" onClick={() => setMobileNavOpen(true)}>
                  <Menu className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="hidden h-9 w-9 p-0 lg:inline-flex" onClick={toggleSidebar} aria-label="Toggle sidebar">
                  {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                </Button>
                <p className="text-sm font-medium text-foreground">Performance Management System</p>
                <div className="hidden min-w-[240px] max-w-sm flex-1 lg:block">
                  <Input placeholder="Search goals, check-ins, meetings" className="h-9 bg-surface/70" />
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                {effectiveRole ? (
                  <span className="hidden rounded-full border border-border/70 bg-surface px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground md:inline-flex">
                    {effectiveRole}
                  </span>
                ) : null}
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
                <div className="relative" ref={notificationsRef}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="relative h-9 w-9 rounded-full p-0"
                    aria-label="Notifications"
                    onClick={() => setNotificationsOpen((prev) => !prev)}
                  >
                    <Bell className="h-4 w-4" />
                    {unreadCount > 0 ? (
                      <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
                        {unreadCount > 9 ? "9+" : unreadCount}
                      </span>
                    ) : null}
                  </Button>
                  {notificationsOpen ? (
                    <div className="absolute right-0 top-11 z-[9999] w-80 rounded-2xl border border-border/80 bg-card p-2.5 shadow-floating">
                      <div className="mb-2 flex items-center justify-between px-2">
                        <p className="text-sm font-semibold text-foreground">Notifications</p>
                        <button
                          type="button"
                          className="text-xs text-primary"
                          onClick={async () => {
                            await notificationsService.markAllRead().catch(() => null);
                            setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
                            setUnreadCount(0);
                          }}
                        >
                          Mark all read
                        </button>
                      </div>
                      <div className="max-h-80 space-y-1 overflow-y-auto px-1">
                        {notifications.length === 0 ? (
                          <p className="px-2 py-6 text-center text-sm text-muted-foreground">No notifications yet.</p>
                        ) : (
                          notifications.map((item) => (
                            <button
                              key={item.id}
                              type="button"
                              onClick={async () => {
                                if (!item.is_read) {
                                  await notificationsService.markRead(item.id).catch(() => null);
                                  setNotifications((prev) => prev.map((row) => (row.id === item.id ? { ...row, is_read: true } : row)));
                                  setUnreadCount((prev) => Math.max(prev - 1, 0));
                                }
                                setNotificationsOpen(false);
                                if (item.action_url) {
                                  router.push(item.action_url);
                                }
                              }}
                              className={cn(
                                "w-full rounded-xl border p-2 text-left",
                                item.is_read ? "border-border/50 bg-surface/40" : "border-primary/25 bg-primary/5"
                              )}
                            >
                              <p className="text-xs font-semibold text-foreground">{item.title}</p>
                              <p className="mt-0.5 text-xs text-muted-foreground">{item.message}</p>
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
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
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
            {canSwitchMode && effectiveRole && (
              <div className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                Viewing as {effectiveRole === "manager" ? "Manager" : "Employee"}
              </div>
            )}
            {children}
          </div>
        </div>
      </main>

      {tourOpen && user ? (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/45 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-5 shadow-floating">
            <p className="text-xs font-semibold uppercase tracking-wide text-primary">Guided Tour</p>
            <h2 className="mt-1 text-lg font-semibold text-foreground">{`Step ${tourStep + 1} of ${(tourStepsByRole[user.role] || []).length}`}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{tourStepsByRole[user.role]?.[tourStep]}</p>
            <div className="mt-4 h-2 w-full rounded bg-muted/60">
              <div
                className="h-2 rounded bg-primary"
                style={{ width: `${((tourStep + 1) / Math.max(tourStepsByRole[user.role]?.length || 1, 1)) * 100}%` }}
              />
            </div>
            <div className="mt-5 flex items-center justify-between">
              <Button
                variant="outline"
                onClick={() => setTourStep((prev) => Math.max(prev - 1, 0))}
                disabled={tourStep === 0}
              >
                Back
              </Button>
              {tourStep < (tourStepsByRole[user.role]?.length || 1) - 1 ? (
                <Button onClick={() => setTourStep((prev) => prev + 1)}>Next</Button>
              ) : (
                <Button
                  onClick={async () => {
                    await authService.completeOnboarding().catch(() => null);
                    patchUser({ first_login: false, onboarding_complete: true });
                    setTourOpen(false);
                  }}
                >
                  Finish Tour
                </Button>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
