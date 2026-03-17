export function HeatmapGrid({ values }: { values: number[] }) {
  return (
    <div className="grid grid-cols-7 gap-2.5">
      {values.map((value, index) => (
        <div
          key={index}
          className="h-9 w-full rounded-lg border border-border/60 shadow-card"
          style={{
            backgroundColor: `color-mix(in oklab, hsl(var(--primary)) ${Math.max(14, Math.min(90, value))}%, hsl(var(--card)))`,
            boxShadow: `inset 0 1px 0 rgb(255 255 255 / 0.18)`,
          }}
          title={`Score ${value}%`}
        />
      ))}
    </div>
  );
}
