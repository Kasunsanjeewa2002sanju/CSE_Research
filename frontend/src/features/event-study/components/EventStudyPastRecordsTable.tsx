import { useMemo, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Download, AlertCircle, ArrowUpDown } from 'lucide-react';
import { exportEventStudyCsv } from '../utils/event-study-export';
import type { EventStudyPerEventItem } from '../types';

export interface EventStudyPastRecordsTableProps {
  items: EventStudyPerEventItem[];
  windowDays?: string;
  warnSmallSample?: boolean;
  smallSampleWarningText?: string;
  isLoading?: boolean;
}

type SortField =
  | 'year'
  | 'election_type'
  | 'event_name'
  | 'aspi_before'
  | 'aspi_after'
  | 'change_pct'
  | 'car'
  | 't_stat'
  | 'p_value'
  | 'corrected_p_val';

export function EventStudyPastRecordsTable({
  items,
  windowDays = '[0,+7]',
  warnSmallSample,
  smallSampleWarningText,
  isLoading,
}: EventStudyPastRecordsTableProps) {
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState<SortField>('year');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const filteredItems = useMemo(() => {
    let result = [...items];
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (it) =>
          it.event_name.toLowerCase().includes(q) ||
          it.election_type.toLowerCase().includes(q) ||
          String(it.year).includes(q)
      );
    }

    result.sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });

    return result;
  }, [items, search, sortField, sortAsc]);

  if (isLoading) {
    return (
      <Card className="h-96 animate-pulse">
        <CardContent className="h-full" />
      </Card>
    );
  }

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="border-border/40 flex flex-row flex-wrap items-center justify-between gap-3 border-b pb-3">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle className="text-base font-semibold">
              Historical Records &amp; Econometric Performance Table
            </CardTitle>
            <Badge variant="outline" className="font-mono text-xs">
              Window {windowDays}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-0.5 text-xs">
            Individual election records: pre/post ASPI levels, market changes, CAR, and Brown-Warner
            / Benjamini-Hochberg statistics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search records..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border-input focus:ring-primary h-8 w-44 rounded-md border bg-background px-2.5 text-xs focus:outline-none focus:ring-1"
          />
          <button
            type="button"
            onClick={() => exportEventStudyCsv(filteredItems)}
            className="border-input text-foreground hover:bg-muted inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 p-4">
        {warnSmallSample && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
            <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <span>
              {smallSampleWarningText ??
                'Sample size below threshold (n < 10): statistical power limited; interpret with caution.'}
            </span>
          </div>
        )}

        <div className="overflow-x-auto rounded-card border border-border">
          <table className="w-full text-left font-mono text-xs">
            <thead className="border-b border-border bg-surface-subtle text-[11px] uppercase text-text-muted">
              <tr>
                <th
                  onClick={() => handleSort('year')}
                  className="cursor-pointer px-3 py-2.5 font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center gap-1">
                    Year <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('election_type')}
                  className="cursor-pointer px-3 py-2.5 font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center gap-1">
                    Type <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('event_name')}
                  className="min-w-[180px] cursor-pointer px-3 py-2.5 font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center gap-1">
                    Event <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('aspi_before')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    ASPI Before <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('aspi_after')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    ASPI After <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('change_pct')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    Change (%) <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('car')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    CAR (%) <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('t_stat')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    t-stat <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('p_value')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    p-val <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th
                  onClick={() => handleSort('corrected_p_val')}
                  className="cursor-pointer px-3 py-2.5 text-right font-semibold hover:text-text-primary"
                >
                  <span className="inline-flex items-center justify-end gap-1">
                    BH FDR (q) <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
                <th className="px-3 py-2.5 text-center font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-border/60 divide-y bg-surface-white">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-xs text-text-muted">
                    No matching event study records found.
                  </td>
                </tr>
              ) : (
                filteredItems.map((r, i) => (
                  <tr key={`${r.event_id}-${i}`} className="hover:bg-blue-ice/30 transition-colors">
                    <td className="px-3 py-2 font-mono text-xs">{r.year}</td>
                    <td className="px-3 py-2 text-xs font-medium">{r.election_type}</td>
                    <td className="px-3 py-2 text-xs font-medium text-text-primary">
                      {r.event_name}
                      {r.is_overlapping && (
                        <span className="py-0.2 ml-1.5 inline-block rounded bg-amber-500/10 px-1 text-[10px] text-amber-700 dark:text-amber-300">
                          Overlapping
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-text-muted">
                      {r.aspi_before > 0
                        ? r.aspi_before.toLocaleString(undefined, {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-text-muted">
                      {r.aspi_after > 0
                        ? r.aspi_after.toLocaleString(undefined, {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">
                      <span
                        className={
                          r.change_pct >= 0
                            ? 'text-primary font-bold'
                            : 'text-slate-600 dark:text-slate-300'
                        }
                      >
                        {r.change_pct > 0 ? `+${r.change_pct}%` : `${r.change_pct}%`}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs font-bold">
                      <span
                        className={
                          r.car >= 0 ? 'text-primary' : 'text-slate-600 dark:text-slate-300'
                        }
                      >
                        {r.car > 0 ? `+${r.car}%` : `${r.car}%`}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-text-muted">
                      {r.t_stat.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-text-muted">
                      {r.p_value}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-text-muted">
                      {r.corrected_p_val}
                    </td>
                    <td className="px-3 py-2 text-center text-xs">
                      <Badge
                        variant={
                          r.corrected_p_val < 0.05
                            ? 'success'
                            : r.p_value < 0.1
                              ? 'warning'
                              : 'outline'
                        }
                        className="px-1.5 py-0 text-[10px]"
                      >
                        {r.significance_badge ?? 'Inconclusive'}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
