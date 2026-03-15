export function HeatmapGrid({ values }: { values: number[] }) {
  return (
    <div className="grid grid-cols-7 gap-2">
      {values.map((value, index) => (
        <div
          key={index}
          className="h-8 w-full rounded-md border border-border/50"
          style={{
            backgroundColor: `color-mix(in oklab, hsl(var(--primary)) ${Math.max(16, Math.min(92, value))}%, hsl(var(--card)))`,
          }}
          title={`Score ${value}%`}
        />
      ))}
    </div>
  );
}
