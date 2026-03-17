import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function SectionWrapper({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-6", className)} {...props}>
      {children}
    </div>
  );
}
