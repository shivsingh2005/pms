export default function Loading() {
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-6 p-8">
      <div className="h-8 w-52 rounded-lg bg-muted" />
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-36 rounded-xl bg-muted" />
        ))}
      </div>
      <div className="h-64 rounded-xl bg-muted" />
      <div className="h-48 rounded-xl bg-muted" />
    </div>
  );
}