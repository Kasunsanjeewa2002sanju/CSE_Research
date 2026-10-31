import React, { useState, useMemo, useRef } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Eye } from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  accessor?: (row: T) => React.ReactNode;
  render?: (val: unknown, row: T) => React.ReactNode;
  sortable?: boolean;
  sortValue?: (row: T) => string | number;
  className?: string;
  defaultVisible?: boolean;
  width?: string;
}

export interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  caption?: string;
  stickyHeader?: boolean;
  virtualized?: boolean;
  rowHeight?: number;
  viewportHeight?: number;
  enableExport?: boolean;
  exportFilename?: string;
  exportFileName?: string;
  emptyMessage?: string;
  keyField?: keyof T | string;
  enableColumnVisibility?: boolean;
  className?: string;
}

export function useCsvExport<T>() {
  const exportToCsv = (columns: Column<T>[], data: T[], filename = 'export.csv') => {
    const headers = columns.map((col) => `"${col.header.replace(/"/g, '""')}"`).join(',');
    const rows = data.map((row) =>
      columns
        .map((col) => {
          const raw = col.sortValue
            ? col.sortValue(row)
            : col.accessor
              ? col.accessor(row)
              : (row as Record<string, unknown>)[col.key];
          const str = typeof raw === 'string' || typeof raw === 'number' ? String(raw) : '';
          return `"${str.replace(/"/g, '""')}"`;
        })
        .join(',')
    );

    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return { exportToCsv };
}

export function Table<T>({
  data,
  columns,
  caption,
  stickyHeader = true,
  virtualized = false,
  rowHeight = 40,
  viewportHeight = 400,
  enableExport = true,
  exportFilename,
  exportFileName,
  emptyMessage = 'No records available.',
  keyField,
  enableColumnVisibility = true,
  className,
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    columns.forEach((c) => {
      initial[c.key] = c.defaultVisible !== false;
    });
    return initial;
  });
  const [showColMenu, setShowColMenu] = useState(false);
  const [scrollTop, setScrollTop] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const effectiveExportFilename = exportFileName || exportFilename || 'research-table.csv';
  const { exportToCsv } = useCsvExport<T>();

  // Sorting
  const sortedData = useMemo(() => {
    if (!sortKey) return data;
    const col = columns.find((c) => c.key === sortKey);
    if (!col) return data;

    const copy = [...data];
    copy.sort((a, b) => {
      let valA: string | number = '';
      let valB: string | number = '';

      if (col.sortValue) {
        valA = col.sortValue(a);
        valB = col.sortValue(b);
      } else {
        const rawA = (a as Record<string, unknown>)[col.key];
        const rawB = (b as Record<string, unknown>)[col.key];
        valA = typeof rawA === 'number' ? rawA : String(rawA || '');
        valB = typeof rawB === 'number' ? rawB : String(rawB || '');
      }

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return copy;
  }, [data, sortKey, sortDirection, columns]);

  const activeCols = useMemo(
    () => columns.filter((c) => visibleColumns[c.key]),
    [columns, visibleColumns]
  );

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDirection === 'asc') setSortDirection('desc');
      else {
        setSortKey(null);
        setSortDirection('asc');
      }
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  // Virtualization calculations
  const totalCount = sortedData.length;
  const startIndex = virtualized ? Math.max(0, Math.floor(scrollTop / rowHeight) - 5) : 0;
  const endIndex = virtualized
    ? Math.min(totalCount, Math.ceil((scrollTop + viewportHeight) / rowHeight) + 5)
    : totalCount;
  const visibleData = virtualized ? sortedData.slice(startIndex, endIndex) : sortedData;
  const paddingTop = virtualized ? startIndex * rowHeight : 0;
  const paddingBottom = virtualized ? (totalCount - endIndex) * rowHeight : 0;

  return (
    <div
      className={cn(
        'space-y-3 rounded-card border border-border bg-surface-card p-4 shadow-soft',
        className
      )}
    >
      {/* Controls Bar: Column Visibility & CSV Export */}
      <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
        {caption && (
          <span className="font-heading text-sm font-semibold text-text-primary">{caption}</span>
        )}

        <div className="ml-auto flex items-center gap-2">
          {enableColumnVisibility && (
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowColMenu(!showColMenu)}
                className="h-7 gap-1.5 font-mono text-xs"
              >
                <Eye className="h-3.5 w-3.5 text-text-muted" />
                <span>Columns</span>
              </Button>

              {showColMenu && (
                <div className="animate-fade-in absolute right-0 z-40 mt-1 w-48 rounded-card border border-border bg-surface-card p-2 font-sans text-xs shadow-elevated">
                  <div className="mb-1 px-1 font-mono text-[11px] text-text-muted">
                    Toggle Columns
                  </div>
                  {columns.map((c) => (
                    <label
                      key={c.key}
                      className="flex cursor-pointer select-none items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-subtle"
                    >
                      <input
                        type="checkbox"
                        checked={visibleColumns[c.key]}
                        onChange={(e) =>
                          setVisibleColumns({ ...visibleColumns, [c.key]: e.target.checked })
                        }
                        className="rounded text-accent focus:ring-accent"
                      />
                      <span className="truncate">{c.header}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

          {enableExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportToCsv(activeCols, sortedData, effectiveExportFilename)}
              className="h-7 gap-1.5 font-mono text-xs"
            >
              <Download className="h-3.5 w-3.5 text-text-muted" />
              <span>Export CSV</span>
            </Button>
          )}
        </div>
      </div>

      {/* Table Container */}
      <div
        ref={scrollRef}
        onScroll={(e) => virtualized && setScrollTop(e.currentTarget.scrollTop)}
        style={virtualized ? { maxHeight: `${viewportHeight}px`, overflowY: 'auto' } : undefined}
        className="border-border/80 overflow-x-auto rounded-button border"
      >
        <table className="w-full text-left font-mono text-xs" role="table">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead
            className={cn(
              'border-b border-border bg-surface-subtle text-[11px] uppercase tracking-wider text-text-muted',
              stickyHeader && 'sticky top-0 z-10'
            )}
          >
            <tr>
              {activeCols.map((col) => {
                const isSorted = sortKey === col.key;
                const canSort = col.sortable || !!col.sortValue;
                return (
                  <th
                    key={col.key}
                    scope="col"
                    style={col.width ? { width: col.width } : undefined}
                    aria-sort={
                      isSorted ? (sortDirection === 'asc' ? 'ascending' : 'descending') : undefined
                    }
                    className={cn('select-none px-4 py-2.5 font-semibold', col.className)}
                  >
                    {canSort ? (
                      <button
                        type="button"
                        onClick={() => handleSort(col.key)}
                        className="transition-standard inline-flex items-center gap-1.5 text-left hover:text-text-primary"
                      >
                        <span>{col.header}</span>
                        {isSorted ? (
                          sortDirection === 'asc' ? (
                            <ArrowUp className="h-3 w-3 text-accent" />
                          ) : (
                            <ArrowDown className="h-3 w-3 text-accent" />
                          )
                        ) : (
                          <ArrowUpDown className="h-3 w-3 text-text-subtle opacity-60" />
                        )}
                      </button>
                    ) : (
                      <span>{col.header}</span>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-border/60 divide-y bg-surface-white">
            {paddingTop > 0 && (
              <tr>
                <td style={{ height: `${paddingTop}px` }} colSpan={activeCols.length} />
              </tr>
            )}

            {visibleData.length === 0 ? (
              <tr>
                <td colSpan={activeCols.length} className="px-4 py-8 text-center text-text-muted">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              visibleData.map((row, idx) => {
                const rowKey = keyField
                  ? String((row as Record<string, unknown>)[keyField as string])
                  : idx;
                return (
                  <tr
                    key={rowKey}
                    className="hover:bg-blue-ice/40 dark:hover:bg-blue-soft/20 transition-standard"
                  >
                    {activeCols.map((col) => {
                      const rawValue = (row as Record<string, unknown>)[col.key];
                      const renderedContent = col.render
                        ? col.render(rawValue, row)
                        : col.accessor
                          ? col.accessor(row)
                          : (rawValue as React.ReactNode);
                      return (
                        <td key={col.key} className={cn('px-4 py-2.5', col.className)}>
                          {renderedContent}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}

            {paddingBottom > 0 && (
              <tr>
                <td style={{ height: `${paddingBottom}px` }} colSpan={activeCols.length} />
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
