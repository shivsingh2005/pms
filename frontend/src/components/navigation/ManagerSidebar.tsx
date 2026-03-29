import { CheckSquare, LayoutDashboard, Presentation, UserCheck, Users, Video } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface ManagerSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const managerNavItems = [
  { href: "/manager-dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/manager/team-dashboard", label: "Team Dashboard", icon: Users },
  { href: "/manager/goals-allotment", label: "Goal Allotment", icon: UserCheck },
  { href: "/manager/approvals", label: "Approvals", icon: CheckSquare },
  { href: "/manager/team-performance", label: "Team Performance", icon: Presentation },
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
