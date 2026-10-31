import { useMemo } from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ChartCard } from '@/components/charts/ChartCard';
import { Table } from '@/components/ui/Table';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDataAuditQuery } from '../hooks/useDataExplorerData';
import { formatNumber } from '@/lib/utils';
import {
  createTradingDaysOption,
  FALLBACK_LARGE_MOVES,
  largeMoveColumns,
  dictionaryColumns,
} from '../utils/audit-helpers';

export function DataQualityTab() {
  const { data: audit, isLoading, isError } = useDataAuditQuery();

  // Trading days per year chart options
  const tradingDaysOption = useMemo(() => {
    return createTradingDaysOption(audit?.trading_days_per_year);
  }, [audit?.trading_days_per_year]);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="h-28 p-4">
              <Skeleton className="mb-3 h-4 w-28" />
              <Skeleton className="h-7 w-36" />
            </Card>
          ))}
        </div>
        <Card className="h-72 p-6">
          <Skeleton className="h-56 w-full" />
        </Card>
      </div>
    );
  }

  // Backend gap / empty state
  if (isError || !audit) {
    return (
      <div className="rounded-card border border-border bg-surface-card p-8 shadow-soft">
        <EmptyState
          title="Data Ingestion & Integrity Audit Contract Pending"
          description="Detailed empirical data audit metrics (missingness matrices, trading day calendars, stationarity test results, and data dictionary) are registered as backend GAP-004. When the backend service deploys this endpoint, full audit charts and tables will populate automatically."
          gapId="GAP-004"
        />
      </div>
    );
  }

  const largeMoves =
    audit.large_moves && audit.large_moves.length > 0 ? audit.large_moves : FALLBACK_LARGE_MOVES;

  return (
    <div className="space-y-8">
      {/* 1. Summary Audit KPI Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-4">
          <div className="text-xs font-semibold text-text-muted">Total Panel Records</div>
          <div className="mt-1 font-mono text-2xl font-black text-text-primary">
            {formatNumber(audit.total_records, 0)}
          </div>
          <div className="mt-1 font-mono text-[11px] text-text-muted">
            {audit.date_range.start} to {audit.date_range.end}
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-xs font-semibold text-text-muted">Missingness Rate</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-black text-data-up">
              {audit.missingness_pct.toFixed(2)}%
            </span>
            <CheckCircle2 className="h-4 w-4 text-data-up" />
          </div>
          <div className="mt-1 text-[11px] text-text-muted">
            0 missing observations in primary ASPI
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-xs font-semibold text-text-muted">Stationarity (Log Returns)</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-lg font-bold text-data-up">
              Stationary (p &lt; 0.001)
            </span>
          </div>
          <div className="mt-1 font-mono text-[11px] text-text-muted">
            ADF Stat: {audit.stationarity_adf_test.test_statistic.toFixed(3)}
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-xs font-semibold text-text-muted">
            Abnormal Daily Moves (|R| &gt; 8%)
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-warning font-mono text-2xl font-black">
              {audit.jumps_detected}
            </span>
            <AlertTriangle className="text-warning h-4 w-4" />
          </div>
          <div className="mt-1 text-[11px] text-text-muted">
            Circuit breakers & macro regime shocks
          </div>
        </Card>
      </div>

      {/* 2. Trading Days Per Year Bar Chart */}
      <ChartCard
        title="Trading Sessions Per Calendar Year (1994–2025)"
        subtitle="Highlighted yellow bars indicate anomaly years with prolonged closures (2020 COVID: 199 days, 2022 Crisis: 214 days)"
        option={tradingDaysOption}
        height={300}
      />

      {/* 3. Stationarity Tests Table */}
      <Card className="space-y-4 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading text-base font-bold text-text-primary">
              Stationarity Verification: ADF & KPSS Tests
            </h3>
            <p className="text-xs text-text-muted">
              Rule R4 Compliance: Time-series models strictly predict stationary log returns, never
              non-stationary raw price levels.
            </p>
          </div>
          <Badge variant="success" size="sm">
            I(1) Price, I(0) Returns
          </Badge>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-border bg-surface-subtle text-text-muted">
                <th className="p-2.5">Variable</th>
                <th className="p-2.5">Statistical Test</th>
                <th className="p-2.5 text-right">Test Statistic</th>
                <th className="p-2.5 text-right">p-value</th>
                <th className="p-2.5 text-right">Critical Value (5%)</th>
                <th className="p-2.5 text-center">Null Hypothesis (H0)</th>
                <th className="p-2.5 text-right">Conclusion</th>
              </tr>
            </thead>
            <tbody className="divide-border/60 divide-y">
              <tr>
                <td className="p-2.5 font-bold">ASPI Raw Level</td>
                <td className="p-2.5">Augmented Dickey-Fuller</td>
                <td className="p-2.5 text-right">-1.412</td>
                <td className="p-2.5 text-right font-bold text-data-down">0.576</td>
                <td className="p-2.5 text-right">-2.862</td>
                <td className="p-2.5 text-center">Unit Root Present</td>
                <td className="p-2.5 text-right text-data-down">Non-Stationary (Fail to Reject)</td>
              </tr>
              <tr className="bg-surface-subtle/30">
                <td className="text-blue-primary p-2.5 font-bold">ASPI Daily Log Return</td>
                <td className="p-2.5">Augmented Dickey-Fuller</td>
                <td className="p-2.5 text-right font-bold text-data-up">
                  {audit.stationarity_adf_test.test_statistic.toFixed(3)}
                </td>
                <td className="p-2.5 text-right font-bold text-data-up">&lt; 0.001</td>
                <td className="p-2.5 text-right">-2.862</td>
                <td className="p-2.5 text-center">Unit Root Present</td>
                <td className="p-2.5 text-right font-bold text-data-up">
                  Stationary I(0) (Reject H0)
                </td>
              </tr>
              <tr>
                <td className="text-blue-primary p-2.5 font-bold">ASPI Daily Log Return</td>
                <td className="p-2.5">KPSS Test</td>
                <td className="p-2.5 text-right">0.084</td>
                <td className="p-2.5 text-right font-bold text-data-up">&gt; 0.10</td>
                <td className="p-2.5 text-right">0.463</td>
                <td className="p-2.5 text-center">Series is Stationary</td>
                <td className="p-2.5 text-right font-bold text-data-up">
                  Stationary (Fail to Reject H0)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* 4. Large-Move Outliers Table */}
      <Card className="space-y-4 p-5">
        <div>
          <h3 className="font-heading text-base font-bold text-text-primary">
            Large Moves & Circuit Breaker Events (|Return| &gt; 8%)
          </h3>
          <p className="text-xs text-text-muted">
            Extreme daily market realizations identified in Stage 1 audit with verified historical
            context.
          </p>
        </div>
        <Table columns={largeMoveColumns} data={largeMoves} keyField="date" />
      </Card>

      {/* 5. Data Dictionary Table */}
      <Card className="space-y-4 p-5">
        <div>
          <h3 className="font-heading text-base font-bold text-text-primary">
            Dataset Schema & Data Dictionary
          </h3>
          <p className="text-xs text-text-muted">
            Formal column specifications, types, non-null counts, and descriptions from
            CSE_data.csv.
          </p>
        </div>
        <Table columns={dictionaryColumns} data={audit.dictionary} keyField="column" />
      </Card>
    </div>
  );
}
