import { CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { formatDateTimeColombo } from '@/utils/formatters';
import type { PipelineRunItem } from '../types';

export interface RunHistoryTableProps {
  runs: PipelineRunItem[];
  isLoading?: boolean;
}

export function RunHistoryTable({ runs, isLoading: _isLoading = false }: RunHistoryTableProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-heading text-sm font-bold text-text-primary">
            Daemon Execution & Polling History
          </h3>
          <p className="text-xs text-text-muted">
            Continuous background polling cron jobs executing RSS ingestions, FinBERT scoring, and market predictions.
          </p>
        </div>
        <span className="font-mono text-xs text-text-muted">
          Showing last <strong className="text-text-primary">{runs.length}</strong> execution cycles
        </span>
      </div>

      <div className="overflow-x-auto rounded-card border border-border bg-surface-white shadow-card">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-surface-subtle text-[11px] font-bold uppercase tracking-wider text-text-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Run ID</th>
              <th scope="col" className="px-3 py-3">Status</th>
              <th scope="col" className="px-3 py-3">Started At (Asia/Colombo)</th>
              <th scope="col" className="px-3 py-3">Completed At</th>
              <th scope="col" className="px-3 py-3 text-right">Duration</th>
              <th scope="col" className="px-4 py-3 text-right">Articles Ingested</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60 font-mono">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-text-muted">
                  No daemon execution logs recorded.
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr key={run.run_id} className="transition-colors hover:bg-surface-subtle/40">
                  {/* Run ID */}
                  <td className="px-4 py-2.5 font-bold text-blue-navy">
                    {run.run_id}
                  </td>

                  {/* Status */}
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
                      <Badge variant="primary" size="sm" className="font-mono text-[10px] uppercase">
                        {run.status}
                      </Badge>
                    </div>
                  </td>

                  {/* Started At */}
                  <td className="px-3 py-2.5 text-text-muted">
                    {formatDateTimeColombo(run.started_at)}
                  </td>

                  {/* Completed At */}
                  <td className="px-3 py-2.5 text-text-muted">
                    {run.completed_at ? formatDateTimeColombo(run.completed_at) : '—'}
                  </td>

                  {/* Duration */}
                  <td className="px-3 py-2.5 text-right font-medium text-text-primary">
                    {run.duration_sec ? `${run.duration_sec.toFixed(1)}s` : '—'}
                  </td>

                  {/* Articles Ingested */}
                  <td className="px-4 py-2.5 text-right font-extrabold text-blue-cobalt">
                    {run.articles_ingested.toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
export default RunHistoryTable;
