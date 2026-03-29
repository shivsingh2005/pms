import { BarChartHorizontal, LayoutDashboard, Lightbulb, Files } from "lucide-react";
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

export function LeadershipSidebar({ pathname, collapsed }: LeadershipSidebarProps) {
  return (
    <div className="space-y-1 px-3">
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
  );
}
