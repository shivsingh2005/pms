interface Row {
  name: string;
  score: number;
  trend: "up" | "down" | "flat";
}

export function StackRankingTable({ rows }: { rows: Row[] }) {
  return (
    <div className="max-h-72 overflow-auto rounded-xl border bg-card">
      <table className="w-full text-left text-sm text-foreground">
        <thead className="sticky top-0 z-10 bg-muted text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Rank</th>
            <th className="px-4 py-3 font-medium">Employee</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium">Trend</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.name} className="border-t transition hover:bg-muted/60">
              <td className="px-4 py-3 font-medium">#{index + 1}</td>
              <td className="px-4 py-3">{row.name}</td>
              <td className="px-4 py-3">{row.score}</td>
              <td className="px-4 py-3 capitalize">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                  row.trend === "up"
                    ? "bg-success/15 text-success"
                    : row.trend === "down"
                      ? "bg-error/15 text-error"
                      : "bg-muted text-muted-foreground"
                }`}
                >
                  {row.trend}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
