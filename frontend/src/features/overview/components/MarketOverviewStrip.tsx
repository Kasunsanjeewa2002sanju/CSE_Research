import { useMemo } from 'react';
import { Activity, Clock, Database, Layers } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { MarketSummary } from '@/api/types';
import { useMarketStatsQuery } from '../hooks/useOverviewData';
import { useLiveMarket } from '@/stores/market-store';
import { formatDateTimeColombo } from '@/utils/formatters';

export interface MarketOverviewStripProps {
  summary?: MarketSummary | null;
  asOfDate?: string;
}

export function MarketOverviewStrip({ summary, asOfDate }: MarketOverviewStripProps) {
  const { data: stats } = useMarketStatsQuery();

  const liveState = useLiveMarket((s) => ({
    freshness: s.derived_freshness_state,
    lastUpdated: s.last_updated,
    connectionStatus: s.connection_status,
  }));

  // Effective freshness state
  const effectiveState = useMemo(() => {
    if (liveState.connectionStatus === 'OFFLINE') return 'OFFLINE';
    if (liveState.connectionStatus === 'POLLING') return 'POLLING';
    return liveState.freshness || stats?.freshness_state || (summary?.is_stale ? 'STALE' : 'CLOSED');
  }, [liveState.connectionStatus, liveState.freshness, stats?.freshness_state, summary?.is_stale]);

  // Derived panel days string from /api/market/stats
  const panelDaysText = useMemo(() => {
    const days = stats?.panel_size_days ?? 7635;
    const startYear = '1994';
    const endYear = stats?.as_of_date
      ? stats.as_of_date.substring(0, 4)
      : asOfDate
        ? asOfDate.substring(0, 4)
        : String(new Date().getFullYear());

    return `Panel: ${days.toLocaleString()} Days (${startYear}–${endYear})`;
  }, [stats?.panel_size_days, stats?.as_of_date, asOfDate]);

  // Annualized volatility
  const volatility =
    stats?.realized_volatility_annualized ?? summary?.realized_volatility_annualized;

  // Real source timestamp in Asia/Colombo
  const asOfColombo = useMemo(() => {
    const raw =
      liveState.lastUpdated ||
      stats?.source_timestamp ||
      summary?.as_of_date ||
      asOfDate;

    if (!raw) return 'Awaiting live stream...';
    return formatDateTimeColombo(raw, true, true);
  }, [liveState.lastUpdated, stats?.source_timestamp, summary?.as_of_date, asOfDate]);

  // Badge variant mapping
  const badgeVariant = useMemo(() => {
    switch (effectiveState) {
      case 'LIVE':
        return 'success';
      case 'DELAYED':
        return 'warning';
      case 'STALE':
        return 'warning';
      case 'OFFLINE':
        return 'danger';
      case 'POLLING':
        return 'accent';
      case 'CLOSED':
      default:
        return 'outline';
    }
  }, [effectiveState]);

  return (
    <div className="bg-surface-subtle/80 border-b border-border px-4 py-2.5 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 font-mono text-xs text-text-muted">
        <div className="flex flex-wrap items-center gap-4 sm:gap-6">
          <div className="flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${effectiveState === 'LIVE' ? 'bg-emerald-500 animate-pulse' : 'bg-accent'}`}
              aria-hidden="true"
            />
            <span className="font-semibold text-text-primary">Market Overview:</span>
            <span>Colombo Stock Exchange</span>
          </div>

          <div className="hidden items-center gap-1 sm:flex">
            <Database className="text-blue-primary h-3.5 w-3.5" aria-hidden="true" />
            <span>{panelDaysText}</span>
          </div>

          <div className="hidden items-center gap-1 md:flex">
            <Layers className="text-blue-primary h-3.5 w-3.5" aria-hidden="true" />
            <span>Benchmarks: ASPI & S&P SL 20</span>
          </div>

          {volatility !== undefined && volatility !== null && (
            <div className="flex items-center gap-1">
              <Activity className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
              <span>Ann. Volatility: {volatility.toFixed(1)}%</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Badge variant={badgeVariant} size="sm">
            {effectiveState}
          </Badge>

          <div className="flex items-center gap-1 text-[11px]" title={`Last updated: ${asOfColombo}`}>
            <Clock className="h-3 w-3 text-text-muted" aria-hidden="true" />
            <span>Data As-Of: {asOfColombo}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
