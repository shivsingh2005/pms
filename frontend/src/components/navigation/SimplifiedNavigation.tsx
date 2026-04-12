"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Target,
  CheckSquare,
  Calendar,
  Star,
  Sprout,
  Users,
  BarChart3,
  Settings,
  Layers,
  TrendingUp,
  Award,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSessionStore } from "@/store/useSessionStore";

interface NavItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
  badge?: string | number;
  badgeColor?: "green" | "red" | "amber" | "blue";
}

/**
 * Simplified Navigation Component
 *
 * PRD FIX 7: Maximum 6 navigation items per role.
 * Removes everything except primary workflow steps.
 * Clean, scannable, purposeful.
 */
export function SimplifiedNavigation() {
  const pathname = usePathname();
  const user = useSessionStore((state) => state.user);
  const [roleExpanded, setRoleExpanded] = useState(false);

  // Define navigation for each role (max 6 items each)
  const navigationByRole: Record<string, NavItem[]> = {
    employee: [
      {
        icon: Home,
        label: "Dashboard",
        href: "/employee/dashboard",
        badge: undefined,
      },
      { icon: Target, label: "Goals", href: "/employee/goals" },
      { icon: CheckSquare, label: "Check-ins", href: "/employee/checkins" },
      { icon: Calendar, label: "Meetings", href: "/employee/meetings" },
      { icon: Star, label: "My Reviews", href: "/employee/reviews" },
      { icon: Sprout, label: "Growth", href: "/employee/growth" },
    ],
    manager: [
      {
        icon: Home,
        label: "Dashboard",
        href: "/manager/dashboard",
        badge: undefined,
      },
      { icon: Users, label: "My Team", href: "/manager/team-dashboard" },
      { icon: Target, label: "Goals", href: "/manager/goals-allotment" },
      { icon: CheckSquare, label: "Goal Approvals", href: "/manager/goal-approvals" },
      { icon: BarChart3, label: "Team Analytics", href: "/manager/team-performance" },
      { icon: Calendar, label: "Meetings", href: "/meetings" },
    ],
    hr: [
      { icon: Home, label: "Dashboard", href: "/hr/dashboard" },
      { icon: Users, label: "People", href: "/hr/people" },
      { icon: BarChart3, label: "Analytics", href: "/hr/analytics" },
      { icon: Calendar, label: "Meetings", href: "/hr/meetings" },
      { icon: Settings, label: "Settings", href: "/hr/settings" },
      { icon: Layers, label: "Reports", href: "/hr/reports" },
    ],
    leadership: [
      { icon: Home, label: "Dashboard", href: "/leadership/dashboard" },
      { icon: Target, label: "Goals", href: "/leadership/goals" },
      { icon: TrendingUp, label: "Trends", href: "/leadership/trends" },
      { icon: Award, label: "Talent", href: "/leadership/talent" },
      { icon: Layers, label: "Reports", href: "/leadership/reports" },
      { icon: Settings, label: "Strategy", href: "/leadership/strategy" },
    ],
  };

  const navItems = navigationByRole[user?.role || "employee"] || navigationByRole.employee;

  const isActive = (href: string) => pathname?.startsWith(href);

  return (
    <nav className="flex flex-col gap-2">
      {/* Navigation Items */}
      {navItems.map((item) => {
        const Icon = item.icon;
        const active = isActive(item.href);

        return (
          <Link key={item.href} href={item.href}>
            <Button
              variant={active ? "default" : "ghost"}
              className="w-full justify-start gap-3 text-left"
              size="sm"
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span
                  className={`flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
                    item.badgeColor === "red"
                      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                      : item.badgeColor === "amber"
                        ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                        : item.badgeColor === "blue"
                          ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                          : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Button>
          </Link>
        );
      })}

      <div className="border-t border-border my-2" />

      {/* Role Toggle for Managers (if applicable) */}
      {["manager", "employee"].includes(user?.role || "") && (
        <div>
          <button
            onClick={() => setRoleExpanded(!roleExpanded)}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <span>Switch Role</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${roleExpanded ? "rotate-180" : ""}`}
            />
          </button>
          {roleExpanded && user?.role === "manager" && (
            <Link href="/employee/dashboard">
              <Button
                variant="ghost"
                className="w-full justify-start gap-3 pl-6 text-left"
                size="sm"
              >
                <Home className="h-4 w-4" />
                View as Employee
              </Button>
            </Link>
          )}
        </div>
      )}

      <div className="border-t border-border my-2" />

      {/* Sign Out */}
      <Button
        variant="ghost"
        className="w-full justify-start gap-3 text-left text-muted-foreground hover:text-foreground"
        size="sm"
        onClick={() => {
          // Handle sign out
          window.location.href = "/api/auth/logout";
        }}
      >
        <LogOut className="h-4 w-4" />
        <span>Sign Out</span>
      </Button>
    </nav>
  );
}

/**
 * Sidebar Container
 * Usage: Wrap SimplifiedNavigation in this container for consistent styling
 */
export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-border bg-card p-4 overflow-y-auto">
      {/* Logo/Brand */}
      <div className="mb-8">
        <h1 className="text-xl font-bold text-foreground">PMS</h1>
        <p className="text-xs text-muted-foreground">Performance Coach</p>
      </div>

      {/* Navigation */}
      <SimplifiedNavigation />
    </aside>
  );
}
