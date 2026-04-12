import { BarChartHorizontal, Files, LayoutDashboard, Lightbulb, Target } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface LeadershipSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const leadershipNavItems = [
  { href: "/leadership/org-dashboard", label: "Org Dashboard", icon: LayoutDashboard },
  { href: "/leadership/performance-trends", label: "Performance Trends", icon: BarChartHorizontal },
  { href: "/leadership/talent-insights", label: "Talent Insights", icon: Lightbulb },
  { href: "/leadership/reports", label: "Reports", icon: Files },
] as const;

const leadershipGoalsNavItems = [
  { href: "/leadership/goals", label: "Cycle Workspace", icon: Target },
  { href: "/leadership/goals/assignments", label: "Manager Cascade", icon: Target },
  { href: "/leadership/goals/progress", label: "Cascade Progress", icon: Target },
] as const;

export function LeadershipSidebar({ pathname, collapsed }: LeadershipSidebarProps) {
  return (
    <div className="space-y-4 px-3">
      <div className="space-y-1">
      {leadershipNavItems.map((item) => {
        const active = pathname === item.href.split("?")[0];
        return (
          <SidebarItem
            key={item.href}
            href={item.href}
            label={item.label}
            active={active}
            icon={item.icon}
            collapsed={collapsed}
          />
        );
      })}
      </div>

      <div className="space-y-1">
        {!collapsed ? <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Goals</p> : null}
        {leadershipGoalsNavItems.map((item) => {
          const active = pathname === item.href.split("?")[0];
          return (
            <SidebarItem
              key={item.href}
              href={item.href}
              label={item.label}
              active={active}
              icon={item.icon}
              collapsed={collapsed}
            />
          );
        })}
      </div>
    </div>
  );
}
