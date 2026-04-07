import type { ComponentType } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface SidebarItemProps {
  href: string;
  label: string;
  active: boolean;
  icon: ComponentType<{ className?: string }>;
  collapsed?: boolean;
}

export function SidebarItem({ href, label, active, icon: Icon, collapsed = false }: SidebarItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      aria-label={label}
      title={collapsed ? label : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        collapsed ? "justify-center px-2" : "",
        active ? "bg-primary/12 text-primary shadow-card" : "text-muted-foreground hover:bg-muted/70 hover:text-foreground",
      )}
    >
      <Icon className={cn("h-4 w-4 transition", active ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
      {!collapsed ? <span>{label}</span> : null}
      {active ? (
        <>
          <motion.div layoutId="nav-pill" className="absolute inset-0 rounded-xl border border-primary/35" />
          <motion.span layoutId="nav-bar" className="absolute -left-1 top-2 bottom-2 w-1 rounded-full bg-primary" />
        </>
      ) : null}
    </Link>
  );
}

