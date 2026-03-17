import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface DataTableColumn<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T, rowIndex: number) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  rows: T[];
  columns: DataTableColumn<T>[];
  rowKey: (row: T, rowIndex: number) => string;
  className?: string;
  emptyState?: ReactNode;
}

export function DataTable<T>({ rows, columns, rowKey, className, emptyState }: DataTableProps<T>) {
  return (
    <div className={cn("overflow-auto rounded-2xl border border-border/70 bg-card/95 shadow-card", className)}>
      <table className="w-full text-left text-sm text-foreground">
        <thead className="sticky top-0 z-10 border-b border-border/70 bg-surface/95 text-muted-foreground backdrop-blur">
          <tr>
            {columns.map((column) => (
              <th key={String(column.key)} className={cn("px-4 py-3 font-medium", column.className)}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="px-4 py-6 text-center text-sm text-muted-foreground" colSpan={columns.length}>
                {emptyState ?? "No records found"}
              </td>
            </tr>
          ) : (
            rows.map((row, rowIndex) => (
              <tr key={rowKey(row, rowIndex)} className="border-t border-border/60 transition hover:bg-muted/45">
                {columns.map((column) => (
                  <td key={String(column.key)} className={cn("px-4 py-3", column.className)}>
                    {column.render
                      ? column.render(row, rowIndex)
                      : String((row as Record<string, unknown>)[String(column.key)] ?? "-")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
