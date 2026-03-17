import { DataTable } from "@/components/ui/data-table";

interface Row {
  name: string;
  score: number;
  trend: "up" | "down" | "flat";
}

export function StackRankingTable({ rows }: { rows: Row[] }) {
  return (
    <DataTable
      rows={rows}
      rowKey={(row) => row.name}
      className="max-h-72"
      columns={[
        {
          key: "rank",
          header: "Rank",
          render: (_, index) => <span className="font-medium">#{index + 1}</span>,
        },
        { key: "name", header: "Employee" },
        {
          key: "score",
          header: "Score",
          render: (row) => <span className="font-medium">{row.score}</span>,
        },
        {
          key: "trend",
          header: "Trend",
          render: (row) => (
            <span
              className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${
                row.trend === "up"
                  ? "bg-success/15 text-success"
                  : row.trend === "down"
                    ? "bg-error/15 text-error"
                    : "bg-muted text-muted-foreground"
              }`}
            >
              {row.trend}
            </span>
          ),
        },
      ]}
    />
  );
}
