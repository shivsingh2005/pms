import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground outline-none ring-0 transition placeholder:text-muted-foreground focus:border-primary/55 focus:ring-2 focus:ring-primary/30",
        className,
      )}
      {...props}
    />
  );
}
