import { CalendarCheck2, Files, LayoutDashboard, Network, Users, UsersRound } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface HRSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const hrNavItems = [
  { href: "/hr-dashboard", label: "HR Dashboard", icon: LayoutDashboard },
  { href: "/hr/employee-directory", label: "Employee Directory", icon: Users },
  { href: "/hr/manager-team", label: "Manager -> Team View", icon: Network },
  { href: "/hr/calibration", label: "Calibration", icon: UsersRound },
  { href: "/hr/meetings", label: "Meetings", icon: CalendarCheck2 },
  { href: "/hr/reports", label: "Reports", icon: Files },
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
