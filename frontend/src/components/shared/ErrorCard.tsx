export function ErrorCard({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950/20">
      <span className="text-2xl">⚠️</span>
      <div>
        <p className="text-sm font-medium text-red-700 dark:text-red-400">
          Something went wrong
        </p>
        <p className="mt-1 font-mono text-xs text-red-600 dark:text-red-500">
          {message}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 text-xs font-medium text-red-600 underline hover:no-underline"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
