import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { formatNumber, formatPercent, formatSampleSize } from '@/utils/formatters';
import type { OverviewSummary } from '../types';

export interface OverviewMetricCardsProps {
  summary?: OverviewSummary;
  isLoading?: boolean;
}

export function OverviewMetricCards({ summary, isLoading }: OverviewMetricCardsProps) {
  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="mb-2 h-8 w-32" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const isUp = summary.daily_return >= 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-muted-foreground font-mono text-xs uppercase">
            ASPI Index Level
          </CardTitle>
          <Badge variant={isUp ? 'market-up' : 'market-down'}>
            {formatPercent(summary.daily_return, 2, true)}
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="text-foreground font-mono text-2xl font-bold">
            {formatNumber(summary.aspi_current, 2)}
          </div>
          <div className="text-muted-foreground mt-1 font-mono text-xs">
            Data As-Of: {summary.data_as_of}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-muted-foreground font-mono text-xs uppercase">
            Sample Event Count
          </CardTitle>
          <Badge variant="outline">{formatSampleSize(summary.sample_size_events)}</Badge>
        </CardHeader>
        <CardContent>
          <div className="text-foreground font-mono text-2xl font-bold">
            {summary.sample_size_events}
          </div>
          <div className="text-muted-foreground mt-1 text-xs">Documented Political Shocks</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-muted-foreground font-mono text-xs uppercase">
            Champion Model (OOS R²)
          </CardTitle>
          <Badge variant="default">{summary.champion_model_name}</Badge>
        </CardHeader>
        <CardContent>
          <div className="text-market-up font-mono text-2xl font-bold">
            {formatPercent(summary.champion_oos_r2, 2, true)}
          </div>
          <div className="text-muted-foreground mt-1 font-mono text-xs">Over Historical Mean</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-muted-foreground font-mono text-xs uppercase">
            Directional Hit Rate
          </CardTitle>
          <Badge variant="default">5-Day Horizon</Badge>
        </CardHeader>
        <CardContent>
          <div className="text-foreground font-mono text-2xl font-bold">
            {formatPercent(summary.champion_directional_accuracy, 2)}
          </div>
          <div className="text-muted-foreground mt-1 text-xs">Rule R3 Drift Verified</div>
        </CardContent>
      </Card>
    </div>
  );
}
