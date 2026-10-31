import { useState, useMemo } from 'react';
import { Download, SlidersHorizontal, Search, ArrowUpDown } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useDataExplorerSeriesQuery } from '../hooks/useDataExplorerData';
import { formatNumber } from '@/lib/utils';
import type { MarketDataPoint } from '../utils/market-calculations';
import {
  exportMarketDataToCsv,
  filterAndSortMarketData,
  type SortField,
  type SortOrder,
} from '../utils/export-helpers';

export function TableExportTab() {
  const { data: rawSeries, isLoading, isError } = useDataExplorerSeriesQuery('All');

  const [searchDate, setSearchDate] = useState('');
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Column visibility states
  const [visibleColumns, setVisibleColumns] = useState({
    date: true,
    aspi: true,
    sp_sl20: true,
    return: true,
    turnover: true,
    volume: true,
  });

  const toggleColumn = (col: keyof typeof visibleColumns) => {
    setVisibleColumns((prev) => ({ ...prev, [col]: !prev[col] }));
  };

  const points: MarketDataPoint[] = useMemo(() => {
    return (rawSeries?.points as MarketDataPoint[]) || [];
  }, [rawSeries]);

  const processedData = useMemo(() => {
    return filterAndSortMarketData(points, searchDate, sortField, sortOrder);
  }, [points, searchDate, sortField, sortOrder]);

  const totalPages = Math.ceil(processedData.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return processedData.slice(start, start + pageSize);
  }, [processedData, page, pageSize]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  if (isLoading) {
    return (
      <Card className="space-y-4 p-6">
        <div className="flex justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="h-96 w-full" />
      </Card>
    );
  }

  if (isError || points.length === 0) {
    return (
      <Card className="p-8">
        <EmptyState
          title="Market Data Table & Export Contract Pending"
          description="The complete historical dataset export and tabular view are registered under GAP-003. When the backend publishes this endpoint, all 7,635 records will be browseable with column filters and one-click CSV export."
          gapId="GAP-003"
        />
      </Card>
    );
  }

  return (
    <Card className="space-y-4 p-5">
      {/* Top Toolbar: Search, Column Picker, Export */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {/* Search by date */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-text-muted" />
            <input
              id="table-search-input"
              name="table-search-input"
              type="text"
              placeholder="Filter by year or date (e.g. 2024)..."
              value={searchDate}
              onChange={(e) => {
                setSearchDate(e.target.value);
                setPage(1);
              }}
              className="h-9 w-64 rounded-button border border-border bg-surface-card pl-8 pr-3 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>

          {/* Quick Column Toggles */}
          <div className="flex items-center gap-1 rounded-button border border-border bg-surface-subtle p-1 font-mono text-xs">
            <SlidersHorizontal className="ml-1 h-3.5 w-3.5 text-text-muted" />
            <button
              type="button"
              onClick={() => toggleColumn('sp_sl20')}
              className={`rounded px-1.5 py-0.5 text-[11px] transition-colors ${visibleColumns.sp_sl20 ? 'text-blue-cobalt bg-surface-card font-bold shadow-soft dark:text-blue-vibrant' : 'text-text-muted hover:text-text-primary'}`}
            >
              S&P SL 20
            </button>
            <button
              type="button"
              onClick={() => toggleColumn('return')}
              className={`rounded px-1.5 py-0.5 text-[11px] transition-colors ${visibleColumns.return ? 'text-blue-cobalt bg-surface-card font-bold shadow-soft dark:text-blue-vibrant' : 'text-text-muted hover:text-text-primary'}`}
            >
              Returns
            </button>
            <button
              type="button"
              onClick={() => toggleColumn('turnover')}
              className={`rounded px-1.5 py-0.5 text-[11px] transition-colors ${visibleColumns.turnover ? 'text-blue-cobalt bg-surface-card font-bold shadow-soft dark:text-blue-vibrant' : 'text-text-muted hover:text-text-primary'}`}
            >
              Turnover
            </button>
            <button
              type="button"
              onClick={() => toggleColumn('volume')}
              className={`rounded px-1.5 py-0.5 text-[11px] transition-colors ${visibleColumns.volume ? 'text-blue-cobalt bg-surface-card font-bold shadow-soft dark:text-blue-vibrant' : 'text-text-muted hover:text-text-primary'}`}
            >
              Volume
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-text-muted">
            Showing <strong>{processedData.length.toLocaleString()}</strong> trading days
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportMarketDataToCsv(processedData)}
            leftIcon={<Download className="h-4 w-4 text-accent" />}
            className="font-mono text-xs"
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Tabular View */}
      <div className="overflow-x-auto rounded-card border border-border">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-border bg-surface-subtle text-text-muted">
              {visibleColumns.date && (
                <th
                  onClick={() => toggleSort('date')}
                  className="cursor-pointer p-3 font-semibold hover:text-text-primary"
                >
                  <div className="flex items-center gap-1">
                    <span>Date</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
              )}
              {visibleColumns.aspi && (
                <th
                  onClick={() => toggleSort('aspi')}
                  className="cursor-pointer p-3 text-right font-semibold hover:text-text-primary"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>ASPI Closing</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
              )}
              {visibleColumns.sp_sl20 && (
                <th className="p-3 text-right font-semibold">S&P SL 20</th>
              )}
              {visibleColumns.return && (
                <th
                  onClick={() => toggleSort('return')}
                  className="cursor-pointer p-3 text-right font-semibold hover:text-text-primary"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Daily Return</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
              )}
              {visibleColumns.turnover && (
                <th
                  onClick={() => toggleSort('turnover')}
                  className="cursor-pointer p-3 text-right font-semibold hover:text-text-primary"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Turnover (LKR)</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
              )}
              {visibleColumns.volume && (
                <th className="p-3 text-right font-semibold">Shares Traded</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-border/60 divide-y">
            {paginatedRows.map((row) => {
              const isPos = (row.return ?? 0) >= 0;
              return (
                <tr key={row.date} className="hover:bg-surface-subtle/50 transition-colors">
                  {visibleColumns.date && <td className="p-3 font-semibold">{row.date}</td>}
                  {visibleColumns.aspi && (
                    <td className="p-3 text-right font-bold text-blue-navy dark:text-blue-vibrant">
                      {formatNumber(row.aspi, 2)}
                    </td>
                  )}
                  {visibleColumns.sp_sl20 && (
                    <td className="p-3 text-right text-text-muted">
                      {row.sp_sl20 !== undefined && row.sp_sl20 !== null
                        ? formatNumber(row.sp_sl20, 2)
                        : '—'}
                    </td>
                  )}
                  {visibleColumns.return && (
                    <td className="p-3 text-right font-bold">
                      {row.return !== undefined && row.return !== null ? (
                        <span className={isPos ? 'text-data-up' : 'text-data-down'}>
                          {isPos ? '+' : ''}
                          {(row.return * 100).toFixed(2)}%
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  )}
                  {visibleColumns.turnover && (
                    <td className="p-3 text-right">{formatNumber(row.turnover, 0)}</td>
                  )}
                  {visibleColumns.volume && (
                    <td className="p-3 text-right text-text-muted">
                      {formatNumber(row.volume, 0)}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div className="flex items-center justify-between pt-2">
        <span className="font-mono text-xs text-text-muted">
          Page <strong>{page}</strong> of <strong>{totalPages}</strong> (
          {processedData.length.toLocaleString()} total rows)
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-xs"
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="text-xs"
          >
            Next
          </Button>
        </div>
      </div>
    </Card>
  );
}
