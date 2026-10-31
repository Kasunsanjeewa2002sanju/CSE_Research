import React, { useState, useRef } from 'react';
import {
  Download,
  Maximize2,
  Minimize2,
  Table as TableIcon,
  BarChart2,
  HelpCircle,
  FileSpreadsheet,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { IconButton } from '@/components/ui/IconButton';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { EChart, EChartRef } from './EChart';
import { ChartDataTableFallback } from './ChartDataTableFallback';
import { cn } from '@/lib/utils';
import type { EChartsOption } from 'echarts';

export interface ChartCardProps {
  title: string;
  subtitle?: string;
  infoTooltip?: string;
  option?: EChartsOption;
  children?: React.ReactNode;
  rangeControls?: React.ReactNode;
  rangeSlot?: React.ReactNode;
  dataTableFallback?: React.ReactNode;
  dataTableData?: Record<string, unknown>[];
  dataTableColumns?: Array<{ key: string; header: string; sortable?: boolean }>;
  onExportCsv?: () => void;
  isLoading?: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  isError?: boolean;
  error?: string | null;
  errorMessage?: string;
  onRetry?: () => void;
  height?: number;
  className?: string;
}

export function ChartCard({
  title,
  subtitle,
  infoTooltip,
  option,
  children,
  rangeControls,
  rangeSlot,
  dataTableFallback,
  dataTableData,
  dataTableColumns,
  onExportCsv,
  isLoading = false,
  isEmpty = false,
  emptyMessage = 'No chart data available for this selection.',
  isError = false,
  error,
  errorMessage,
  onRetry,
  height = 340,
  className,
}: ChartCardProps) {
  const [showTable, setShowTable] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const chartRef = useRef<EChartRef>(null);

  const effectiveError = error || errorMessage;
  const hasError = isError || !!effectiveError;
  const effectiveRangeControls = rangeSlot || rangeControls;

  const handleExportPng = () => {
    if (!chartRef.current) return;
    const dataUrl = chartRef.current.exportToPng();
    if (!dataUrl) return;

    const link = document.createElement('a');
    link.download = `${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-chart.png`;
    link.href = dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const hasTableFallback = !!dataTableFallback || (dataTableData && dataTableData.length > 0);

  return (
    <Card
      className={cn(
        'flex flex-col space-y-4 p-5 transition-all',
        isFullscreen &&
          'fixed inset-4 z-50 overflow-auto border-2 border-accent bg-surface-card shadow-2xl',
        className
      )}
    >
      {/* Header Bar */}
      <div className="border-border/60 flex flex-col justify-between gap-3 border-b pb-3 sm:flex-row sm:items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="font-heading text-base font-bold tracking-tight text-text-primary">
              {title}
            </h3>
            {infoTooltip && (
              <span
                className="transition-standard cursor-help text-text-subtle hover:text-text-primary"
                title={infoTooltip}
                role="tooltip"
              >
                <HelpCircle className="h-4 w-4" />
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs leading-relaxed text-text-muted">{subtitle}</p>}
        </div>

        {/* Toolbar & Controls */}
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {effectiveRangeControls && <div className="mr-1">{effectiveRangeControls}</div>}

          {/* Toggle Accessible Table */}
          {hasTableFallback && (
            <IconButton
              variant="outline"
              size="sm"
              onClick={() => setShowTable(!showTable)}
              aria-label={
                showTable ? 'Switch to graphic chart view' : 'Switch to accessible data table view'
              }
              title={showTable ? 'Show Chart' : 'Show Accessible Data Table'}
            >
              {showTable ? (
                <BarChart2 className="h-3.5 w-3.5" />
              ) : (
                <TableIcon className="h-3.5 w-3.5" />
              )}
            </IconButton>
          )}

          {/* Export PNG */}
          <IconButton
            variant="outline"
            size="sm"
            onClick={handleExportPng}
            aria-label="Export chart as high-resolution PNG image"
            title="Export PNG"
          >
            <Download className="h-3.5 w-3.5" />
          </IconButton>

          {onExportCsv && (
            <IconButton
              variant="outline"
              size="sm"
              onClick={onExportCsv}
              aria-label="Export chart underlying data as CSV"
              title="Export CSV"
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
            </IconButton>
          )}

          <IconButton
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
            aria-label={isFullscreen ? 'Exit fullscreen chart view' : 'Expand chart to fullscreen'}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
          </IconButton>
        </div>
      </div>

      {/* Main Chart or Accessible Table Body */}
      <div className="flex min-h-[260px] w-full flex-1 flex-col justify-center">
        {isLoading ? (
          <div className="space-y-3 p-4">
            <Skeleton variant="card" className="h-60" />
            <div className="flex justify-between">
              <Skeleton variant="text" className="w-24" />
              <Skeleton variant="text" className="w-32" />
            </div>
          </div>
        ) : hasError ? (
          <ErrorState
            message={effectiveError || 'Failed to compute chart series'}
            onRetry={onRetry}
          />
        ) : isEmpty ? (
          <EmptyState message={emptyMessage} />
        ) : showTable && hasTableFallback ? (
          <div className="py-2">
            {dataTableFallback || (
              <ChartDataTableFallback
                data={dataTableData || []}
                columns={dataTableColumns || []}
                caption={`${title} Data Table Fallback`}
              />
            )}
          </div>
        ) : children ? (
          <div role="img" aria-label={`Chart showing ${title}`}>
            {children}
          </div>
        ) : option ? (
          <div role="img" aria-label={`Chart showing ${title}`}>
            <EChart
              ref={chartRef}
              option={option}
              style={{ height: isFullscreen ? 'calc(100vh - 160px)' : height, width: '100%' }}
            />
          </div>
        ) : (
          <EmptyState message="No chart configuration provided." />
        )}
      </div>

      {/* Honest UI Footer Note */}
      <div className="border-border/40 mt-2 flex items-center justify-between border-t pt-2 font-mono text-[11px] text-text-subtle">
        <span>Historical association, not causation</span>
        <span>Colombo Stock Exchange ASPI</span>
      </div>
    </Card>
  );
}
