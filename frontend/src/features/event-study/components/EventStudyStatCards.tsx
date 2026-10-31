import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react';
import { formatPercent, formatPValue } from '@/utils/formatters';
import type { EventStudyCaarResponse } from '../types';

export interface EventStudyStatCardsProps {
  caarData?: EventStudyCaarResponse;
  isLoading?: boolean;
}

export function EventStudyStatCards({ caarData, isLoading }: EventStudyStatCardsProps) {
  if (isLoading || !caarData) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-muted/40 h-24 animate-pulse rounded-xl" />
        ))}
      </div>
    );
  }

  const stats = caarData.caar_stats;
  const caarVal =
    stats?.caar ?? (caarData.data.length > 0 ? caarData.data[caarData.data.length - 1].caar : 0);
  const tStat = stats?.t_stat ?? 0;
  const pVal = stats?.t_pval ?? 1;
  const permPVal = stats?.permutation_pval ?? caarData.p_value_permutation;
  const bhPVal = stats?.t_pval_bh ?? pVal;
  const n = caarData.event_count;
  const isSmallSample = caarData.warn_small_sample ?? n < (caarData.sample_size_threshold ?? 10);
  const warningText =
    caarData.small_sample_warning_text ??
    'Sample size below threshold (n < 10): statistical power limited; interpret with caution';

  return (
    <div className="space-y-3">
      {/* Small sample warning chip */}
      {isSmallSample && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3.5 py-2 text-xs text-amber-800 dark:text-amber-200"
        >
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <span className="font-semibold uppercase tracking-wider">Small Sample Advisory:</span>
          <span>{warningText}</span>
        </div>
      )}

      {/* Grid of KPI Stat Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {/* 1. Cumulative Average Abnormal Return */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              Mean CAAR
            </span>
            <div
              className={`font-mono text-xl font-bold ${caarVal >= 0 ? 'text-primary' : 'text-slate-600 dark:text-slate-300'}`}
            >
              {formatPercent(caarVal, 2, true)}
            </div>
            <span className="text-muted-foreground block text-[10px]">
              Window {caarData.window_days}
            </span>
          </CardContent>
        </Card>

        {/* 2. t-Statistic */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              t-Statistic
            </span>
            <div className="text-foreground font-mono text-xl font-bold">{tStat.toFixed(2)}</div>
            <span className="text-muted-foreground block text-[10px]">Brown-Warner (1985)</span>
          </CardContent>
        </Card>

        {/* 3. Raw p-Value */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              p-Value (Raw)
            </span>
            <div className="text-foreground font-mono text-xl font-bold">{formatPValue(pVal)}</div>
            <span className="text-muted-foreground block text-[10px]">Two-tailed t-test</span>
          </CardContent>
        </Card>

        {/* 4. Permutation Placebo p-Value */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              Permutation p
            </span>
            <div className="text-foreground font-mono text-xl font-bold">
              {formatPValue(permPVal)}
            </div>
            <span className="text-muted-foreground block text-[10px]">10,000 placebo draws</span>
          </CardContent>
        </Card>

        {/* 5. Corrected p-Value (BH FDR) */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              BH FDR (q)
            </span>
            <div className="text-foreground font-mono text-xl font-bold">
              {formatPValue(bhPVal)}
            </div>
            <span className="text-muted-foreground block text-[10px]">Benjamini-Hochberg</span>
          </CardContent>
        </Card>

        {/* 6. Sample Size & Significance Status */}
        <Card className="border-border/80 shadow-sm">
          <CardContent className="space-y-1.5 p-3">
            <span className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
              Sample (n) &amp; Status
            </span>
            <div className="flex items-center gap-2">
              <span className="text-foreground font-mono text-xl font-bold">n = {n}</span>
            </div>
            <div>
              {bhPVal < 0.05 ? (
                <Badge variant="success" className="gap-1 px-1.5 py-0 text-[10px]">
                  <CheckCircle2 className="h-3 w-3" /> Significant
                </Badge>
              ) : pVal < 0.1 ? (
                <Badge variant="warning" className="gap-1 px-1.5 py-0 text-[10px]">
                  <AlertCircle className="h-3 w-3" /> Marginal
                </Badge>
              ) : (
                <Badge variant="secondary" className="gap-1 px-1.5 py-0 text-[10px]">
                  <HelpCircle className="h-3 w-3" /> Inconclusive
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
