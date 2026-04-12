import Link from "next/link";

export function EmptyState({
  icon,
  title,
  sub,
  action,
  actionHref,
}: {
  icon: string;
  title: string;
  sub?: string;
  action?: string;
  actionHref?: string;
}) {
  return (
    <div className="py-10 text-center">
      <p className="mb-3 text-4xl">{icon}</p>
      <p className="text-sm font-medium">{title}</p>
      {sub && (
        <p className="mt-1 text-xs text-muted-foreground">
          {sub}
        </p>
      )}
      {action && actionHref && (
        <Link
          href={actionHref}
          className="mt-3 inline-block text-xs text-primary hover:underline"
        >
          {action} -&gt;
        </Link>
      )}
    </div>
  );
}
