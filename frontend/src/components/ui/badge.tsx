import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-transparent bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary ring-1 ring-primary/15",
        className,
      )}
      {...props}
    />
  );
}
