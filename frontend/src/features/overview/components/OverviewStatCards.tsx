import { useMemo, useEffect, useRef, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { Sparkline } from '@/components/charts/Sparkline';
import { useMeta } from '@/context/MetaContext';
import {
  useMarketStatsQuery,
  useMarketSeriesQuery,
} from '@/features/overview/hooks/useOverviewData';
import { useLiveMarket, marketStore } from '@/stores/market-store';
import {
  formatNumber,
  formatPercent,
  formatLKR,
  formatVolume,
  formatDateTimeColombo,
} from '@/utils/formatters';
import { useTickAnimation, useThrottledSparkline } from '../hooks/useOverviewLive';
import { Link } from 'react-router-dom';

// ============================================================================
// 1. ASPI Index Live StatCard
// ============================================================================

interface CardProps {
  onRetry?: () => void;
  isOverallLoading?: boolean;
  isOverallError?: boolean;
}

export function AspiStatCard({ onRetry, isOverallLoading, isOverallError }: CardProps) {
  const { getMetricDefinition } = useMeta();

  // Fine-grained memoised selector: only updates when ASPI or connection changes
  const aspiData = useLiveMarket((s) => ({
    value: s.snapshot?.aspi_value,
    change: s.snapshot?.aspi_change,
    pctChange: s.snapshot?.aspi_percent_change,
    prevClose: s.snapshot?.aspi_previous_close,
    freshness: s.derived_freshness_state,
    lastUpdated: s.last_updated,
    sparkline: s.sparklines.aspi,
    connectionStatus: s.connection_status,
  }));

  const { data: stats } = useMarketStatsQuery();
  const throttledSparkline = useThrottledSparkline(aspiData.sparkline, 1000);

  // Value resolution (live stream snapshot -> stats baseline -> undefined)
  const displayValue = aspiData.value ?? stats?.baseline_aspi;
  const { flashClassName } = useTickAnimation(displayValue);

  // Real live CSE change and percent change (without predicted 1D return)
  const change = aspiData.change;
  const pctChange = aspiData.pctChange ?? (stats?.daily_return_pct !== undefined ? stats.daily_return_pct : 0);
  const isUp = change != null ? change >= 0 : (pctChange != null ? pctChange >= 0 : true);

  const deltaFormatted = useMemo(() => {
    if (change != null && pctChange != null) {
      const sign = change >= 0 ? '+' : '';
      return `${sign}${formatNumber(change, 2)} (${formatPercent(pctChange, 2, true, true)})`;
    }
    if (pctChange != null) {
      return formatPercent(pctChange, 4, true, true);
    }
    return '—';
  }, [change, pctChange]);

  // As-of timestamp formatted in Asia/Colombo with seconds
  const asOfText = useMemo(() => {
    const raw = aspiData.lastUpdated || stats?.source_timestamp || stats?.as_of_date;
    return formatDateTimeColombo(raw, true);
  }, [aspiData.lastUpdated, stats?.source_timestamp, stats?.as_of_date]);

  const definition =
    getMetricDefinition('aspi')?.definition ||
    'All Share Price Index (ASPI): Primary capitalization-weighted benchmark of the CSE.';

  const isClosed = aspiData.freshness === 'CLOSED';
  const isStale = aspiData.freshness === 'STALE';

  return (
    <StatCard
      label="ASPI Index"
      value={displayValue !== undefined ? formatNumber(displayValue, 2) : '—'}
      valueClassName={flashClassName}
      delta={{
        value: deltaFormatted,
        isPositive: isUp,
        direction: isUp ? 'up' : 'down',
      }}
      sparkline={
        throttledSparkline.length > 1 ? (
          <Sparkline
            data={throttledSparkline}
            color={isUp ? '#0F9D6B' : '#D93A3A'}
            width={90}
            height={26}
          />
        ) : undefined
      }
      asOfLabel={isClosed ? `Last Close: ${asOfText}` : `As of: ${asOfText}`}
      statusState={aspiData.freshness}
      isStale={isStale}
      isLoading={isOverallLoading && displayValue === undefined}
      isError={isOverallError && displayValue === undefined}
      onRetry={onRetry}
      glossaryTerm="ASPI"
      glossaryDefinition={definition}
    />
  );
}

// ============================================================================
// 2. S&P Sri Lanka 20 Live StatCard
// ============================================================================

export function Sp20StatCard({ onRetry, isOverallLoading, isOverallError }: CardProps) {
  const { getMetricDefinition } = useMeta();

  // Fine-grained memoised selector for S&P SL 20
  const sp20Data = useLiveMarket((s) => ({
    value: s.snapshot?.sp20_value,
    change: s.snapshot?.sp20_change,
    pctChange: s.snapshot?.sp20_percent_change,
    prevClose: s.snapshot?.sp20_previous_close,
    freshness: s.derived_freshness_state,
    lastUpdated: s.last_updated,
    sparkline: s.sparklines.sp20,
  }));

  const { data: stats } = useMarketStatsQuery();
  const throttledSparkline = useThrottledSparkline(sp20Data.sparkline, 1000);

  const displayValue = sp20Data.value ?? stats?.baseline_sp20;
  const { flashClassName } = useTickAnimation(displayValue);

  // Real live CSE S&P SL 20 change and percent change (without predicted 5D return)
  const change = sp20Data.change;
  const pctChange = sp20Data.pctChange ?? 0;
  const isUp = change != null ? change >= 0 : (pctChange != null ? pctChange >= 0 : true);

  const deltaFormatted = useMemo(() => {
    if (change != null && pctChange != null) {
      const sign = change >= 0 ? '+' : '';
      return `${sign}${formatNumber(change, 2)} (${formatPercent(pctChange, 2, true, true)})`;
    }
    if (pctChange != null) {
      return formatPercent(pctChange, 2, true, true);
    }
    return '—';
  }, [change, pctChange]);

  const asOfText = useMemo(() => {
    const raw = sp20Data.lastUpdated || stats?.source_timestamp || stats?.as_of_date;
    return formatDateTimeColombo(raw, true);
  }, [sp20Data.lastUpdated, stats?.source_timestamp, stats?.as_of_date]);

  const definition =
    getMetricDefinition('sp_sl20')?.definition ||
    'S&P Sri Lanka 20: Measures 20 largest and most liquid stocks. Available from 2012.';

  const isClosed = sp20Data.freshness === 'CLOSED';
  const isStale = sp20Data.freshness === 'STALE';

  return (
    <StatCard
      label="S&P Sri Lanka 20"
      value={displayValue !== undefined ? formatNumber(displayValue, 2) : '—'}
      valueClassName={flashClassName}
      delta={{
        value: deltaFormatted,
        isPositive: isUp,
        direction: isUp ? 'up' : 'down',
      }}
      sparkline={
        throttledSparkline.length > 1 ? (
          <Sparkline data={throttledSparkline} color="#00B8D9" width={90} height={26} />
        ) : undefined
      }
      asOfLabel={isClosed ? `Last Close: ${asOfText}` : `As of: ${asOfText}`}
      badgeText="Post-2012"
      statusState={sp20Data.freshness}
      isStale={isStale}
      isLoading={isOverallLoading && displayValue === undefined}
      isError={isOverallError && displayValue === undefined}
      onRetry={onRetry}
      glossaryTerm="S&P SL 20"
      glossaryDefinition={definition}
    />
  );
}

// ============================================================================
// 3. Equity Turnover Live StatCard
// ============================================================================

export function TurnoverStatCard({ onRetry, isOverallLoading, isOverallError }: CardProps) {
  const { getMetricDefinition } = useMeta();

  // Fine-grained memoised selector for turnover
  const turnoverData = useLiveMarket((s) => ({
    turnover: s.snapshot?.market_turnover,
    freshness: s.derived_freshness_state,
    lastUpdated: s.last_updated,
    sparkline: s.sparklines.turnover,
  }));

  const { data: stats } = useMarketStatsQuery();
  const throttledSparkline = useThrottledSparkline(turnoverData.sparkline, 1000);

  const displayTurnover = turnoverData.turnover ?? stats?.equity_turnover_lkr;
  const { flashClassName } = useTickAnimation(displayTurnover);

  const asOfText = useMemo(() => {
    const raw = turnoverData.lastUpdated || stats?.source_timestamp || stats?.as_of_date;
    return formatDateTimeColombo(raw, true);
  }, [turnoverData.lastUpdated, stats?.source_timestamp, stats?.as_of_date]);

  const definition =
    getMetricDefinition('turnover')?.definition ||
    'Daily equity turnover in Sri Lankan Rupees (LKR).';

  const isClosed = turnoverData.freshness === 'CLOSED';
  const isStale = turnoverData.freshness === 'STALE';

  return (
    <StatCard
      label="Equity Turnover"
      value={displayTurnover !== undefined ? formatLKR(displayTurnover) : '—'}
      valueClassName={flashClassName}
      delta={{
        value: displayTurnover ? `LKR ${Math.round(displayTurnover).toLocaleString()}` : 'Market Turnover',
        direction: 'neutral',
      }}
      sparkline={
        throttledSparkline.length > 1 ? (
          <Sparkline data={throttledSparkline} color="#1B5CD6" width={90} height={26} />
        ) : undefined
      }
      asOfLabel={isClosed ? `Last Close: ${asOfText}` : `As of: ${asOfText}`}
      statusState={turnoverData.freshness}
      isStale={isStale}
      isLoading={isOverallLoading && displayTurnover === undefined}
      isError={isOverallError && displayTurnover === undefined}
      onRetry={onRetry}
      glossaryTerm="Turnover"
      glossaryDefinition={definition}
    />
  );
}

// ============================================================================
// 4. Shares Traded Live StatCard
// ============================================================================

export function SharesStatCard({ onRetry, isOverallLoading, isOverallError }: CardProps) {
  const { getMetricDefinition } = useMeta();

  // Fine-grained memoised selector for volume
  const sharesData = useLiveMarket((s) => ({
    shares: s.snapshot?.shares_traded,
    trades: s.snapshot?.total_trades,
    freshness: s.derived_freshness_state,
    lastUpdated: s.last_updated,
    sparkline: s.sparklines.shares,
  }));

  const { data: stats } = useMarketStatsQuery();
  const throttledSparkline = useThrottledSparkline(sharesData.sparkline, 1000);

  const displayShares = sharesData.shares ?? stats?.shares_traded;
  const { flashClassName } = useTickAnimation(displayShares);

  const asOfText = useMemo(() => {
    const raw = sharesData.lastUpdated || stats?.source_timestamp || stats?.as_of_date;
    return formatDateTimeColombo(raw, true);
  }, [sharesData.lastUpdated, stats?.source_timestamp, stats?.as_of_date]);

  const definition =
    getMetricDefinition('shares_traded')?.definition ||
    'Total volume of shares transacted in daily trading session.';

  const isClosed = sharesData.freshness === 'CLOSED';
  const isStale = sharesData.freshness === 'STALE';

  return (
    <StatCard
      label="Shares Traded"
      value={displayShares !== undefined ? formatVolume(displayShares) : '—'}
      valueClassName={flashClassName}
      delta={{
        value: sharesData.trades ? `${formatNumber(sharesData.trades, 0)} Trades` : 'Total Shares',
        direction: 'neutral',
      }}
      sparkline={
        throttledSparkline.length > 1 ? (
          <Sparkline data={throttledSparkline} color="#53627A" width={90} height={26} />
        ) : undefined
      }
      asOfLabel={isClosed ? `Last Close: ${asOfText}` : `As of: ${asOfText}`}
      statusState={sharesData.freshness}
      isStale={isStale}
      isLoading={isOverallLoading && displayShares === undefined}
      isError={isOverallError && displayShares === undefined}
      onRetry={onRetry}
      glossaryTerm="Shares Traded"
      glossaryDefinition={definition}
    />
  );
}

// ============================================================================
// Master Container: OverviewStatCards
// ============================================================================

export function OverviewStatCards() {
  const {
    isLoading: statsLoading,
    isError: statsError,
    refetch: refetchStats,
  } = useMarketStatsQuery();

  const { data: seriesData } = useMarketSeriesQuery('1M');

  // Seed store sparklines from historical series on initial load if not yet populated
  useEffect(() => {
    if (seriesData?.points && seriesData.points.length > 0) {
      const recent = seriesData.points.slice(-30);
      marketStore.seedSparklines({
        aspi: recent.map((p) => p.aspi),
        sp20: recent.filter((p) => p.sp_sl20 != null).map((p) => p.sp_sl20 as number),
        turnover: recent.filter((p) => p.turnover_lkr != null || p.turnover != null).map((p) => (p.turnover_lkr ?? p.turnover ?? 0)),
        shares: recent.filter((p) => p.volume != null).map((p) => p.volume as number),
      });
    }
  }, [seriesData]);

  // Real-time 1-second update interval dedicated exclusively to these Key Market Stat Cards
  useEffect(() => {
    // Initial fetch on mount
    marketStore.pollLatest();

    const interval = setInterval(() => {
      marketStore.pollLatest();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Screen reader polite live announcement (throttled)
  const currentAspi = useLiveMarket((s) => s.snapshot?.aspi_value);
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>('');
  const lastAnnouncedRef = useRef<number>(0);

  useEffect(() => {
    if (currentAspi !== undefined) {
      const now = Date.now();
      if (now - lastAnnouncedRef.current > 6000) {
        lastAnnouncedRef.current = now;
        setLiveAnnouncement(`Market update: ASPI level is ${formatNumber(currentAspi, 2)}`);
      }
    }
  }, [currentAspi]);

  return (
    <div className="space-y-4">
      {/* Off-screen accessibility live region */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {liveAnnouncement}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="text-blue-primary h-5 w-5" aria-hidden="true" />
          <h2 className="font-heading text-lg font-bold text-text-primary">
            Key Market Performance Indicators
          </h2>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live (1s)
          </span>
        </div>
        <Link to="/data" className="text-xs font-semibold text-accent hover:underline">
          Explore Full Historical Series &rarr;
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AspiStatCard
          onRetry={() => refetchStats()}
          isOverallLoading={statsLoading}
          isOverallError={statsError}
        />
        <Sp20StatCard
          onRetry={() => refetchStats()}
          isOverallLoading={statsLoading}
          isOverallError={statsError}
        />
        <TurnoverStatCard
          onRetry={() => refetchStats()}
          isOverallLoading={statsLoading}
          isOverallError={statsError}
        />
        <SharesStatCard
          onRetry={() => refetchStats()}
          isOverallLoading={statsLoading}
          isOverallError={statsError}
        />
      </div>
    </div>
  );
}
