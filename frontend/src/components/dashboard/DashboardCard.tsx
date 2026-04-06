import type { HTMLAttributes } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface DashboardCardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export function DashboardCard({ className, children, interactive = true, ...props }: DashboardCardProps) {
  return (
    <motion.div whileHover={interactive ? { y: -1 } : undefined} transition={{ duration: 0.2, ease: "easeOut" }}>
      <Card
        className={cn(
          "rounded-xl border border-border bg-card shadow-soft transition hover:shadow-elevated",
          className,
        )}
        {...props}
      >
        {children}
      </Card>
    </motion.div>
  );
}

