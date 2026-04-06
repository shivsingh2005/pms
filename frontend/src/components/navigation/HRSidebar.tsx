import { BarChartHorizontal, LayoutDashboard, Trophy, Users, Video, FileText } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface HRSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const hrNavItems = [
  { href: "/hr/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/hr/employee-directory", label: "Employee Directory", icon: Users },
  { href: "/hr/analytics", label: "Analytics", icon: BarChartHorizontal },
  { href: "/hr/calibration", label: "Calibration", icon: Trophy },
  { href: "/meetings", label: "Meetings", icon: Video },
  { href: "/hr/reports", label: "Reports", icon: FileText },
] as const;

export function HRSidebar({ pathname, collapsed }: HRSidebarProps) {
  return (
    <div className="space-y-1 px-3">
      {hrNavItems.map((item) => {
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
