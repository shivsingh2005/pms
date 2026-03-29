import { Building2, LayoutDashboard, Settings, ShieldCheck, Users } from "lucide-react";
import { SidebarItem } from "@/components/navigation/SidebarItem";

interface AdminSidebarProps {
  pathname: string;
  collapsed: boolean;
}

const adminNavItems = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/users", label: "User Management", icon: Users },
  { href: "/admin/roles", label: "Role Management", icon: ShieldCheck },
  { href: "/admin/organization", label: "Organization Structure", icon: Building2 },
  { href: "/admin/settings", label: "System Settings", icon: Settings },
] as const;

export function AdminSidebar({ pathname, collapsed }: AdminSidebarProps) {
  return (
    <div className="space-y-1 px-3">
      {adminNavItems.map((item) => {
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
