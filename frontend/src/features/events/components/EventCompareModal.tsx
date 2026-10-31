import { useEffect, useRef, useMemo } from 'react';
import { echarts } from '@/components/charts/echarts-setup';
import { Dialog } from '@/components/ui/Dialog';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Layers, X } from 'lucide-react';
import type { MarketSeriesPoint, PoliticalEvent } from '@/api/types';
import {
  alignAspiPath,
  createCompareChartOption,
  type AlignedEventPath,
} from '../utils/compare-helpers';
import { getEventTypeColor } from '../utils/timeline-helpers';

export interface EventCompareModalProps {
  events: PoliticalEvent[];
  fullSeries: MarketSeriesPoint[];
  isOpen: boolean;
  onClose: () => void;
  onRemoveEvent?: (eventId: string) => void;
}

export function EventCompareModal({
  events,
  fullSeries,
  isOpen,
  onClose,
  onRemoveEvent,
}: EventCompareModalProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // Align paths for all selected events
  const alignedPaths = useMemo<AlignedEventPath[]>(() => {
    return events
      .map((e) => alignAspiPath(e, fullSeries, 20))
      .filter((p): p is AlignedEventPath => p !== null);
  }, [events, fullSeries]);

  const option = useMemo(() => {
    return createCompareChartOption(alignedPaths);
  }, [alignedPaths]);

  useEffect(() => {
    if (!isOpen || !chartRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, null, { renderer: 'canvas' });
    }

    chartInstance.current.setOption(option, true);

    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, [isOpen, option]);

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Empirical Event Comparison (Rule FR11)"
      className="w-full max-w-4xl"
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <p className="text-muted text-sm">
            Relative ASPI paths normalized to 100.0 at reaction date (t = 0). Evaluated over [-20,
            +20] trading day window.
          </p>
          <div className="flex items-center gap-2">
            <span className="bg-bg-muted text-text rounded px-2 py-1 font-mono text-xs">
              Selected: {events.length}/3
            </span>
          </div>
        </div>

        {/* Selected Event Badges */}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {events.map((e) => {
            const palette = getEventTypeColor(e.category);
            const aligned = alignedPaths.find((ap) => ap.event.id === e.id);
            return (
              <div
                key={e.id}
                className="bg-bg-surface flex flex-col justify-between rounded-lg border border-border p-3"
              >
                <div>
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <Badge
                      variant="outline"
                      className="text-[10px]"
                      style={{ borderColor: palette.primary, color: palette.primary }}
                    >
                      {e.category}
                    </Badge>
                    {onRemoveEvent && events.length > 1 && (
                      <button
                        onClick={() => onRemoveEvent(e.id)}
                        className="text-muted hover:text-text p-0.5"
                        aria-label={`Remove ${e.name} from comparison`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                  <h4 className="text-text line-clamp-1 text-xs font-semibold">{e.name}</h4>
                  <div className="text-muted mt-0.5 font-mono text-[11px]">Reaction: {e.date}</div>
                </div>

                <div className="border-border/60 mt-3 grid grid-cols-2 gap-1 border-t pt-2 text-[11px]">
                  <div>
                    <span className="text-muted block text-[10px]">CAR [-3, +3]</span>
                    <span
                      className={`font-mono font-semibold ${
                        (aligned?.carMinus3Plus3 ?? 0) >= 0 ? 'text-up' : 'text-down'
                      }`}
                    >
                      {(aligned?.carMinus3Plus3 ?? 0) >= 0 ? '+' : ''}
                      {aligned?.carMinus3Plus3.toFixed(2)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted block text-[10px]">Sample (n)</span>
                    <span className="text-text font-mono font-semibold">
                      {aligned?.sampleDays ?? 0} days
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Comparison Chart */}
        <div className="bg-bg-surface rounded-xl border border-border p-4">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-text flex items-center gap-1.5 text-xs font-semibold">
              <Layers className="h-3.5 w-3.5 text-accent" />
              Aligned Cumulative Trajectory (Base 100 at t = 0)
            </h4>
            <span className="text-muted font-mono text-[10px]">Normalized Index Ratio</span>
          </div>
          <div
            ref={chartRef}
            style={{ width: '100%', height: 320 }}
            role="img"
            aria-label="Comparative ASPI paths aligned at reaction date t=0"
          />
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-muted text-[11px]">
            Historical statistical association does not imply direct causation.
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close Comparison
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
