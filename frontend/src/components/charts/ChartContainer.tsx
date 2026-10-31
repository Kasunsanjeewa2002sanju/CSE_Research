import React, { useState } from 'react';
import { Table, BarChart2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { formatSampleSize } from '@/utils/formatters';

export interface ChartContainerProps {
  title: string;
  ariaLabel: string;
  sampleSize?: number;
  asOfDate?: string;
  uncertaintyDescription?: string;
  children: React.ReactNode;
  dataTableFallback?: React.ReactNode;
  className?: string;
}

export function ChartContainer({
  title,
  ariaLabel,
  sampleSize,
  asOfDate,
  uncertaintyDescription,
  children,
  dataTableFallback,
  className,
}: ChartContainerProps) {
  const [showTable, setShowTable] = useState(false);

  return (
    <div
      className={cn(
        'bg-card flex flex-col space-y-4 rounded-lg border border-border p-5 shadow-sm',
        className
      )}
    >
      <div className="border-border/60 flex flex-wrap items-center justify-between gap-2 border-b pb-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-foreground font-heading text-base font-semibold">{title}</h3>
            {sampleSize !== undefined && (
              <span className="bg-muted text-muted-foreground rounded px-2 py-0.5 font-mono text-xs">
                {formatSampleSize(sampleSize)}
              </span>
            )}
          </div>
          <div className="text-muted-foreground flex items-center gap-3 font-mono text-xs">
            {asOfDate && <span>As of: {asOfDate}</span>}
            {uncertaintyDescription && (
              <span className="text-market-accent">• {uncertaintyDescription}</span>
            )}
          </div>
        </div>

        {dataTableFallback && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTable(!showTable)}
            aria-label={showTable ? 'Switch to graphical chart' : 'Switch to accessible data table'}
            className="h-8 gap-1.5 font-mono text-xs"
          >
            {showTable ? (
              <>
                <BarChart2 className="h-3.5 w-3.5" aria-hidden="true" />
                View Graphical Chart
              </>
            ) : (
              <>
                <Table className="h-3.5 w-3.5" aria-hidden="true" />
                View Data Table (WCAG)
              </>
            )}
          </Button>
        )}
      </div>

      <div
        role="img"
        aria-label={ariaLabel}
        className="flex min-h-[280px] w-full flex-1 flex-col justify-center"
      >
        {showTable && dataTableFallback ? dataTableFallback : children}
      </div>

      <div className="text-muted-foreground border-border/40 border-t pt-1 text-right font-mono text-[11px]">
        Historical association, not causation. All intervals empirical.
      </div>
    </div>
  );
}
