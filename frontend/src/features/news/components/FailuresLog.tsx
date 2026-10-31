import { AlertTriangle, ExternalLink, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { formatDateTimeColombo } from '@/utils/formatters';
import type { FailureLogItem } from '../types';

export interface FailuresLogProps {
  failures: FailureLogItem[];
  isLoading?: boolean;
}

export function FailuresLog({ failures, isLoading: _isLoading = false }: FailuresLogProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-heading text-sm font-bold text-text-primary">
            Feed Failures & Anomaly Diagnostics Log
          </h3>
          <p className="text-xs text-text-muted">
            Detailed network inspection logs for unverified, failing, or degraded Sri Lankan news feeds.
          </p>
        </div>
        <Badge
          variant={failures.length > 0 ? 'warning' : 'neutral'}
          size="sm"
          className="font-mono text-xs"
        >
          {failures.length} Active Failures / Warnings
        </Badge>
      </div>

      <div className="overflow-x-auto rounded-card border border-border bg-surface-white shadow-card">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-surface-subtle text-[11px] font-bold uppercase tracking-wider text-text-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Severity</th>
              <th scope="col" className="px-4 py-3">Feed Name & Target</th>
              <th scope="col" className="px-3 py-3 font-mono">Status / HTTP</th>
              <th scope="col" className="px-4 py-3">Root Cause & Diagnostic Message</th>
              <th scope="col" className="px-3 py-3">Last Checked (Asia/Colombo)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {failures.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-text-muted">
                  All monitored feeds are operating normally with zero connection failures.
                </td>
              </tr>
            ) : (
              failures.map((item, idx) => {
                const isCritical = item.severity === 'critical' || item.status === 'error';

                return (
                  <tr
                    key={idx}
                    className={`transition-colors hover:bg-surface-subtle/40 ${
                      isCritical ? 'bg-red-50/20' : 'bg-amber-50/15'
                    }`}
                  >
                    {/* Severity Badge */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold">
                        {isCritical ? (
                          <>
                            <XCircle className="h-4 w-4 text-red-600" aria-hidden="true" />
                            <span className="text-red-700 uppercase">Critical</span>
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="h-4 w-4 text-amber-600" aria-hidden="true" />
                            <span className="text-amber-700 uppercase">Degraded</span>
                          </>
                        )}
                      </div>
                    </td>

                    {/* Feed Name & Target */}
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-1 font-heading font-bold text-text-primary">
                          <span>{item.feed_name}</span>
                          {item.url && (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-text-muted hover:text-blue-cobalt"
                              title="Inspect URL"
                            >
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                        <span className="font-mono text-[10px] text-text-muted truncate max-w-xs">
                          {item.url}
                        </span>
                      </div>
                    </td>

                    {/* Status Code */}
                    <td className="px-3 py-3 font-mono">
                      <Badge
                        variant={item.status_code === 200 ? 'warning' : 'danger'}
                        size="sm"
                        className="font-mono text-[10px]"
                      >
                        HTTP {item.status_code}
                      </Badge>
                    </td>

                    {/* Diagnostic Message */}
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-mono text-xs font-semibold text-red-800">
                          {item.error_message}
                        </span>
                        <span className="text-[10px] text-text-muted">
                          {item.status_code === 403
                            ? 'Cloudflare WAF / anti-bot challenge blocking feed request.'
                            : item.status_code === 404
                            ? 'Endpoint removed or migrated by media publisher.'
                            : item.status_code === 520
                            ? 'Origin server returned unknown response error.'
                            : 'Publisher returned HTML webpage instead of RSS/XML.'}
                        </span>
                      </div>
                    </td>

                    {/* Last Checked */}
                    <td className="px-3 py-3 font-mono text-[11px] text-text-muted">
                      {formatDateTimeColombo(item.last_checked)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
export default FailuresLog;
