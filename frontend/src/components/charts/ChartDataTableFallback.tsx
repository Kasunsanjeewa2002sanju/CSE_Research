import React from 'react';
import { cn } from '@/lib/utils';

export interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T | ((row: T) => React.ReactNode);
  key?: string;
  accessor?: (row: T) => React.ReactNode;
  className?: string;
}

export interface ChartDataTableFallbackProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  caption: string;
  className?: string;
}

export function ChartDataTableFallback<T>({
  data,
  columns,
  caption,
  className,
}: ChartDataTableFallbackProps<T>) {
  return (
    <div className={cn('overflow-x-auto rounded-md border border-border', className)}>
      <table className="w-full text-left font-mono text-xs" aria-label={caption}>
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-muted/50 text-muted-foreground border-b border-border text-[10px] uppercase">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} scope="col" className={cn('px-3 py-2 font-semibold', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="border-border/60 divide-y">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-muted-foreground px-3 py-4 text-center">
                No series data available.
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-muted/30 transition-colors">
                {columns.map((col, colIdx) => {
                  const key = (col.key || col.accessorKey) as keyof T;
                  const val =
                    typeof col.accessorKey === 'function'
                      ? col.accessorKey(row)
                      : typeof col.accessor === 'function'
                        ? col.accessor(row)
                        : (row[key] as React.ReactNode);

                  return (
                    <td key={colIdx} className={cn('px-3 py-2', col.className)}>
                      {val}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
