import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SectionContainerProps extends HTMLAttributes<HTMLDivElement> {
  columns?: "single" | "dashboard";
}

export function SectionContainer({ className, columns = "single", children, ...props }: SectionContainerProps) {
  return (
    <section
      className={cn(
        "grid gap-6",
        columns === "dashboard" ? "grid-cols-1 xl:grid-cols-12" : "grid-cols-1",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}
