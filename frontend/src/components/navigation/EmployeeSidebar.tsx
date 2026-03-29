import { CalendarCheck, ClipboardList, LayoutDashboard, Sparkles, Target } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface EmployeeSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const employeeNavItems = [
  { href: "/employee-dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/goals", label: "My Goals", icon: Target },
  { href: "/employee/checkins", label: "Check-ins", icon: CalendarCheck },
  { href: "/reviews", label: "Reviews", icon: ClipboardList },
  { href: "/employee-dashboard?panel=ai-assistant", label: "AI Assistant", icon: Sparkles },
] as const;

export function EmployeeSidebar({ pathname, collapsed }: EmployeeSidebarProps) {
  return (
    <div className="space-y-1 px-3">
      {employeeNavItems.map((item) => {
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
