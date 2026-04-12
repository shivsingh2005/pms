import { CalendarCheck, LayoutDashboard, Target, Trophy, UserCheck, Users, Video } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface ManagerSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const managerNavItems = [
  { href: "/manager/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/manager/team-dashboard", label: "My Team", icon: Users },
  { href: "/manager/goals-allotment", label: "Goal Assignment", icon: UserCheck },
  { href: "/manager/goal-approvals", label: "Goal Approvals", icon: Target },
  { href: "/manager/approvals", label: "Approvals", icon: CalendarCheck },
  { href: "/manager/team-performance", label: "Team Performance", icon: Trophy },
  { href: "/meetings", label: "Meetings", icon: Video },
] as const;

export function ManagerSidebar({ pathname, collapsed }: ManagerSidebarProps) {
  return (
    <div className="space-y-1 px-3">
      {managerNavItems.map((item) => {
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
