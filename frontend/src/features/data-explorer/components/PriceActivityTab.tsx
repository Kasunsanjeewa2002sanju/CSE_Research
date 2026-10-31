import { useState, useMemo } from 'react';
import { Calendar, Info, Eye, EyeOff } from 'lucide-react';
import { ChartCard } from '@/components/charts/ChartCard';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useDataExplorerSeriesQuery } from '../hooks/useDataExplorerData';
import { useEventsListQuery } from '@/features/events/hooks/useEventsData';
import { useMeta } from '@/context/MetaContext';
import {
  normalizeSpSl20,
  calculateRollingVolatility,
  filterPointsByPreset,
  RangePreset,
  MarketDataPoint,
} from '../utils/market-calculations';
import {
  createPriceOption,
  createReturnsOption,
  createVolatilityOption,
  createVolumeOption,
} from '../utils/chart-options';

export function PriceActivityTab() {
  const [scaleType, setScaleType] = useState<'linear' | 'log'>('linear');
  const [activeRange, setActiveRange] = useState<RangePreset>('1Y');
  const [showSpSl20, setShowSpSl20] = useState(true);
  const [showElectionMarkers, setShowElectionMarkers] = useState(true);
  const [volatilityWindow, setVolatilityWindow] = useState<number>(20);

  const {
    data: rawSeries,
    isLoading: seriesLoading,
    isError: seriesError,
  } = useDataExplorerSeriesQuery('All');
  const { data: eventsData } = useEventsListQuery();
  const { getMetricDefinition, asOfDate } = useMeta();

  // Raw data points or empty
  const allPoints: MarketDataPoint[] = useMemo(() => {
    return (rawSeries?.points as MarketDataPoint[]) || [];
  }, [rawSeries]);

  // Filtered by active preset
  const filteredPoints = useMemo(() => {
    return filterPointsByPreset(allPoints, activeRange);
  }, [allPoints, activeRange]);

  // Normalized S&P SL 20
  const normalizedSp = useMemo(() => {
    return normalizeSpSl20(filteredPoints);
  }, [filteredPoints]);

  // Rolling volatility
  const rollingVol = useMemo(() => {
    return calculateRollingVolatility(filteredPoints, volatilityWindow);
  }, [filteredPoints, volatilityWindow]);

  // Election marklines
  const electionMarkLines = useMemo(() => {
    if (!showElectionMarkers || !eventsData?.items) return [];
    return eventsData.items.map((ev) => ({
      name: ev.name,
      xAxis: ev.event_date,
      label: {
        formatter: ev.name,
        position: 'insideEndTop',
        fontSize: 10,
        color: '#0A2A66',
      },
      lineStyle: {
        color: '#1B5CD6',
        type: 'dashed',
        width: 1.5,
      },
    }));
  }, [showElectionMarkers, eventsData]);

  // Chart 1: ASPI Price & Normalized S&P SL 20 Option
  const priceOption = useMemo(() => {
    return createPriceOption({
      filteredPoints,
      normalizedSp,
      showSpSl20,
      scaleType,
      electionMarkLines,
    });
  }, [filteredPoints, normalizedSp, showSpSl20, scaleType, electionMarkLines]);

  // Chart 2: Daily Returns
  const returnsOption = useMemo(() => {
    return createReturnsOption(filteredPoints);
  }, [filteredPoints]);

  // Chart 3: Rolling Volatility
  const volOption = useMemo(() => {
    return createVolatilityOption({ rollingVol, volatilityWindow });
  }, [rollingVol, volatilityWindow]);

  // Chart 4: Turnover & Volume
  const volumeOption = useMemo(() => {
    return createVolumeOption(filteredPoints);
  }, [filteredPoints]);

  // Loading Skeleton
  if (seriesLoading) {
    return (
      <div className="space-y-6">
        <div className="h-96 rounded-card border border-border bg-surface-card p-6">
          <Skeleton className="mb-4 h-6 w-48" />
          <Skeleton className="h-72 w-full" />
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-72 rounded-card border border-border bg-surface-card p-6">
            <Skeleton className="h-56 w-full" />
          </div>
          <div className="h-72 rounded-card border border-border bg-surface-card p-6">
            <Skeleton className="h-56 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // Backend gap / Empty state
  if (seriesError || allPoints.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface-card p-8 shadow-soft">
        <EmptyState
          title="Historical Market Series Contract Pending"
          description="High-frequency ASPI and S&P SL 20 price, returns, and turnover series are registered as backend GAP-003. When the backend service publishes this endpoint, full area charts, log/linear toggles, and election marklines will render automatically."
          gapId="GAP-003"
        />
      </div>
    );
  }

  const aspiDefinition =
    getMetricDefinition('aspi')?.definition ||
    'All Share Price Index: Broad market capitalization index.';
  const asOf = asOfDate || '2025-12-31';

  return (
    <div className="space-y-8">
      {/* Primary ASPI & S&P SL 20 Area Chart */}
      <ChartCard
        title="Colombo Stock Exchange (ASPI) Price Series"
        subtitle={`Daily closing prices with gradient fill and S&P SL 20 comparative overlay (As of ${asOf})`}
        infoTooltip={aspiDefinition}
        option={priceOption}
        height={400}
        rangeControls={
          <div className="flex flex-wrap items-center gap-2">
            {/* Range Presets */}
            <div className="flex rounded-button border border-border bg-surface-subtle p-0.5">
              {(['1M', '3M', '6M', '1Y', '5Y', 'All'] as RangePreset[]).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setActiveRange(preset)}
                  className={`rounded-button px-2.5 py-1 text-xs font-semibold transition-colors ${
                    activeRange === preset
                      ? 'bg-blue-cobalt text-white shadow-soft dark:bg-blue-vibrant'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {preset}
                </button>
              ))}
            </div>

            {/* Log / Linear Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setScaleType((prev) => (prev === 'linear' ? 'log' : 'linear'))}
              className="font-mono text-xs"
            >
              Scale: {scaleType.toUpperCase()}
            </Button>

            {/* S&P SL 20 Overlay Toggle */}
            <Button
              variant={showSpSl20 ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => setShowSpSl20((prev) => !prev)}
              leftIcon={
                showSpSl20 ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />
              }
              className="text-xs"
            >
              S&P SL 20
            </Button>

            {/* Election Markers Toggle */}
            <Button
              variant={showElectionMarkers ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => setShowElectionMarkers((prev) => !prev)}
              leftIcon={<Calendar className="h-3.5 w-3.5" />}
              className="text-xs"
            >
              Election Stages
            </Button>
          </div>
        }
      />

      {/* S&P SL 20 Footnote Callout */}
      {showSpSl20 && (
        <div className="border-blue-primary/20 bg-blue-ice/30 dark:bg-blue-navy/20 flex items-center gap-2 rounded-card border p-3 font-mono text-xs text-blue-navy dark:text-blue-vibrant">
          <Info className="h-4 w-4 shrink-0 text-accent" />
          <span>
            <strong>Note on S&P Sri Lanka 20:</strong> Launched June 18, 2012. For historical visual
            comparison, S&P SL 20 is mathematically normalised to the ASPI level at its first
            available observation date.
          </span>
        </div>
      )}

      {/* Secondary Chart Grid: Returns, Volatility & Turnover */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Daily Returns */}
        <ChartCard
          title="Daily Return Distribution"
          subtitle="Log return percentage per trading day (Green = Positive, Red = Negative)"
          infoTooltip="r_t = ln(P_t / P_{t-1})"
          option={returnsOption}
          height={280}
        />

        {/* Rolling Volatility */}
        <ChartCard
          title="Annualized Rolling Volatility"
          subtitle={`Trading day volatility annualized using sqrt(252) factor (Window: ${volatilityWindow} Days)`}
          infoTooltip="std(r_{t-W:t}) * sqrt(252) * 100%"
          option={volOption}
          height={280}
          rangeControls={
            <div className="flex items-center gap-1 rounded-button border border-border bg-surface-subtle p-0.5">
              {[20, 60, 120].map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setVolatilityWindow(w)}
                  className={`rounded-button px-2 py-0.5 text-xs font-semibold ${
                    volatilityWindow === w
                      ? 'bg-accent font-bold text-accent-foreground'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {w}D
                </button>
              ))}
            </div>
          }
        />
      </div>

      {/* Turnover and Shares Traded Dual Axis */}
      <ChartCard
        title="Market Activity: Equity Turnover & Shares Traded"
        subtitle="Turnover (LKR, Left Axis) and Shares Volume (Right Axis) with synchronized crosshair"
        option={volumeOption}
        height={260}
      />
    </div>
  );
}
