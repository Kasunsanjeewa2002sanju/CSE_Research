import { useState } from 'react';
import { AlertCircle, CheckCircle, ExternalLink, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { formatDateTimeColombo } from '@/utils/formatters';
import type { NewsFeedItem } from '../types';

export interface FeedHealthTableProps {
  feeds: NewsFeedItem[];
  isLoading?: boolean;
}

export function FeedHealthTable({ feeds, isLoading: _isLoading = false }: FeedHealthTableProps) {
  const [filter, setFilter] = useState<'all' | 'active' | 'issues'>('all');

  const failingFeeds = feeds.filter((f) => f.status !== 'active' || (f.error_count ?? 0) > 0 || Boolean(f.last_error));
  const activeFeeds = feeds.filter((f) => f.status === 'active' && !f.last_error);

  const displayedFeeds =
    filter === 'active' ? activeFeeds : filter === 'issues' ? failingFeeds : feeds;

  return (
    <div className="space-y-4">
      {/* Alert banner if there are failing/degraded feeds */}
      {failingFeeds.length > 0 && (
        <div className="flex items-start gap-3 rounded-card border border-amber-300 bg-amber-50/70 p-4 text-xs text-amber-900 shadow-soft">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
          <div className="flex-1 space-y-1">
            <h4 className="font-heading font-bold text-amber-950">
              {failingFeeds.length} Feed Sources Require Attention
            </h4>
            <p className="leading-relaxed text-amber-800">
              The ingestion daemon flagged HTTP errors, non-RSS HTML responses, or empty payloads
              across {failingFeeds.map((f) => f.name).join(', ')}. Articles from these feeds are temporarily held or falling back to secondary queries.
            </p>
          </div>
        </div>
      )}

      {/* Table controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-1.5" role="tablist" aria-label="Feed filter">
          <button
            type="button"
            role="tab"
            aria-selected={filter === 'all'}
            onClick={() => setFilter('all')}
            className={`rounded-button px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === 'all'
                ? 'bg-blue-navy text-white shadow-soft'
                : 'bg-surface-subtle text-text-muted hover:text-text-primary'
            }`}
          >
            All Feeds ({feeds.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={filter === 'active'}
            onClick={() => setFilter('active')}
            className={`rounded-button px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === 'active'
                ? 'bg-blue-navy text-white shadow-soft'
                : 'bg-surface-subtle text-text-muted hover:text-text-primary'
            }`}
          >
            Active & Verified ({activeFeeds.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={filter === 'issues'}
            onClick={() => setFilter('issues')}
            className={`rounded-button px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === 'issues'
                ? 'bg-amber-600 text-white shadow-soft'
                : 'bg-surface-subtle text-text-muted hover:text-text-primary'
            }`}
          >
            Failing & Degraded ({failingFeeds.length})
          </button>
        </div>

        <div className="font-mono text-xs text-text-muted">
          Total 24h Yield: <strong className="text-text-primary">{feeds.reduce((acc, f) => acc + (f.article_count_24h || 0), 0)} articles</strong>
        </div>
      </div>

      {/* Feeds Table */}
      <div className="overflow-x-auto rounded-card border border-border bg-surface-white shadow-card">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-surface-subtle text-[11px] font-bold uppercase tracking-wider text-text-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Feed Name & Type</th>
              <th scope="col" className="px-3 py-3">Status</th>
              <th scope="col" className="px-3 py-3">HTTP Code</th>
              <th scope="col" className="px-3 py-3">Last Checked (Asia/Colombo)</th>
              <th scope="col" className="px-3 py-3 text-right">24h Items</th>
              <th scope="col" className="px-3 py-3 text-right">Errors</th>
              <th scope="col" className="px-4 py-3">Last Error / Diagnostics</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {displayedFeeds.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-muted">
                  No feeds match the selected filter.
                </td>
              </tr>
            ) : (
              displayedFeeds.map((feed) => {
                const isError = feed.status === 'error';
                const isDegraded = feed.status === 'degraded';
                const isActive = feed.status === 'active';

                return (
                  <tr
                    key={feed.id}
                    className={`transition-colors hover:bg-surface-subtle/50 ${
                      isError ? 'bg-red-50/20' : isDegraded ? 'bg-amber-50/20' : ''
                    }`}
                  >
                    {/* Feed Name & Type */}
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-1.5 font-heading font-bold text-text-primary">
                          <span>{feed.name}</span>
                          {feed.url && (
                            <a
                              href={feed.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-text-muted hover:text-blue-cobalt"
                              title="Inspect RSS URL"
                            >
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                        <span className="font-mono text-[10px] uppercase text-text-muted">
                          {feed.feed_type || 'RSS'}
                        </span>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-1.5">
                        {isActive && <CheckCircle className="h-4 w-4 text-emerald-600" aria-hidden="true" />}
                        {isDegraded && <AlertCircle className="h-4 w-4 text-amber-600" aria-hidden="true" />}
                        {isError && <XCircle className="h-4 w-4 text-red-600" aria-hidden="true" />}
                        <span
                          className={`font-mono font-semibold capitalize ${
                            isActive
                              ? 'text-emerald-700'
                              : isDegraded
                              ? 'text-amber-700'
                              : 'text-red-700'
                          }`}
                        >
                          {feed.status}
                        </span>
                      </div>
                    </td>

                    {/* HTTP Code */}
                    <td className="px-3 py-3 font-mono">
                      <Badge
                        variant={feed.status_code === 200 ? 'primary' : 'warning'}
                        size="sm"
                        className="font-mono text-[10px]"
                      >
                        {feed.status_code || 200}
                      </Badge>
                    </td>

                    {/* Last Checked */}
                    <td className="px-3 py-3 font-mono text-[11px] text-text-muted">
                      {formatDateTimeColombo(feed.last_polled_at)}
                    </td>

                    {/* 24h Items */}
                    <td className="px-3 py-3 text-right font-mono font-semibold text-text-primary">
                      {feed.article_count_24h.toLocaleString()}
                    </td>

                    {/* Error Count */}
                    <td className="px-3 py-3 text-right font-mono">
                      <span className={feed.error_count ? 'font-bold text-red-600' : 'text-text-muted'}>
                        {feed.error_count ?? 0}
                      </span>
                    </td>

                    {/* Last Error / Diagnostics */}
                    <td className="px-4 py-3">
                      {feed.last_error ? (
                        <span
                          className="line-clamp-1 max-w-xs font-mono text-[11px] text-red-700"
                          title={feed.last_error}
                        >
                          {feed.last_error}
                        </span>
                      ) : (
                        <span className="font-mono text-[11px] text-emerald-700">Healthy</span>
                      )}
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
export default FeedHealthTable;
