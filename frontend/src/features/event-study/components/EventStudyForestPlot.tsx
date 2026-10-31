import { useMemo } from 'react';
import { EChart } from '@/components/charts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { buildForestPlotOption } from '../utils/chart-options';
import type { EventStudyPerEventItem } from '../types';

export interface EventStudyForestPlotProps {
  items: EventStudyPerEventItem[];
  windowDays?: string;
  isLoading?: boolean;
}

export function EventStudyForestPlot({
  items,
  windowDays = '[0,+7]',
  isLoading,
}: EventStudyForestPlotProps) {
  const forestOption = useMemo(() => {
    return buildForestPlotOption(items);
  }, [items]);

  if (isLoading) {
    return (
      <Card className="h-80 animate-pulse">
        <CardContent className="h-full" />
      </Card>
    );
  }

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="border-border/40 flex flex-row flex-wrap items-center justify-between gap-2 border-b pb-3">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle className="text-base font-semibold">
              Event Study Forest Plot: CAR per Election
            </CardTitle>
            <Badge variant="outline" className="font-mono text-xs">
              Window {windowDays}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-0.5 text-xs">
            Cross-event distribution of Cumulative Abnormal Return (CAR) with 95% Brown-Warner
            confidence intervals.
          </p>
        </div>
        <Badge variant="secondary" className="text-xs">
          {items.length} Events Evaluated
        </Badge>
      </CardHeader>

      <CardContent className="p-4">
        {items.length === 0 ? (
          <div className="text-muted-foreground py-12 text-center text-xs">
            No event study records match the selected category and window.
          </div>
        ) : (
          <div className="w-full">
            <EChart
              option={forestOption}
              height={Math.max(340, Math.min(500, items.length * 20))}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
