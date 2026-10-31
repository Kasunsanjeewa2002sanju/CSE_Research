import { useState, useMemo } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ZoomIn, ZoomOut, RotateCcw, Calendar } from 'lucide-react';
import type { PoliticalEvent } from '@/api/types';
import {
  groupEventsByCategory,
  getTimelineBounds,
  calculateDateOffset,
  getEventTypeColor,
} from '../utils/timeline-helpers';

export interface EventsTimelineViewProps {
  events: PoliticalEvent[];
  onSelectEvent: (event: PoliticalEvent) => void;
  selectedEventId?: string;
}

export function EventsTimelineView({
  events,
  onSelectEvent,
  selectedEventId,
}: EventsTimelineViewProps) {
  const [zoomLevel, setZoomLevel] = useState<number>(1); // 1x to 3x

  const groups = useMemo(() => groupEventsByCategory(events), [events]);
  const bounds = useMemo(() => getTimelineBounds(events), [events]);

  const years = useMemo(() => {
    const list: number[] = [];
    for (let y = bounds.minYear; y <= bounds.maxYear; y += 2) {
      list.push(y);
    }
    return list;
  }, [bounds]);

  const handleZoomIn = () => setZoomLevel((z) => Math.min(3, z + 0.5));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(1, z - 0.5));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="space-y-4">
      {/* Zoom Controls & Legend */}
      <div className="bg-bg-surface flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border p-3">
        <div className="flex items-center gap-3">
          <span className="text-text text-xs font-semibold">Zoom Timeline:</span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoomLevel <= 1}
              aria-label="Zoom out timeline"
              className="h-7 px-2"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </Button>
            <span className="text-muted px-2 font-mono text-xs">{zoomLevel.toFixed(1)}x</span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoomLevel >= 3}
              aria-label="Zoom in timeline"
              className="h-7 px-2"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>
            {zoomLevel > 1 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetZoom}
                className="text-muted hover:text-text h-7 gap-1 text-xs"
              >
                <RotateCcw className="h-3 w-3" />
                Reset
              </Button>
            )}
          </div>
        </div>

        {/* Legend in blue family & accent */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {groups.map((g) => {
            const palette = getEventTypeColor(g.category);
            return (
              <div key={g.category} className="flex items-center gap-1.5">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: palette.primary }}
                />
                <span className="text-muted">{g.category}</span>
                <span className="text-muted/80 font-mono text-[10px]">({g.events.length})</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scrollable Timeline Canvas */}
      <div className="bg-bg-surface overflow-x-auto rounded-xl border border-border p-4 shadow-sm">
        <div
          style={{ width: `${100 * zoomLevel}%`, minWidth: '700px' }}
          className="relative transition-all duration-200"
        >
          {/* Year Scale Header */}
          <div className="border-border/80 relative mb-6 h-8 border-b">
            {years.map((y) => {
              const leftPct = calculateDateOffset(`${y}-01-01`, bounds.minYear, bounds.maxYear);
              return (
                <div
                  key={y}
                  className="absolute top-0 flex -translate-x-1/2 transform flex-col items-center"
                  style={{ left: `${leftPct}%` }}
                >
                  <span className="text-muted font-mono text-[10px]">{y}</span>
                  <div className="mt-1 h-2 w-px bg-border" />
                </div>
              );
            })}
          </div>

          {/* Grouped Tracks */}
          <div className="space-y-8">
            {groups.map((group) => {
              const palette = getEventTypeColor(group.category);
              return (
                <div key={group.category} className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className="px-2.5 py-0.5 text-xs font-semibold"
                      style={{
                        borderColor: palette.primary,
                        color: palette.primary,
                        backgroundColor: palette.light,
                      }}
                    >
                      {group.category} ({group.events.length})
                    </Badge>
                  </div>

                  {/* Horizontal Track */}
                  <div className="bg-bg-muted/30 border-border/50 relative h-14 rounded-lg border">
                    {/* Background Grid Lines */}
                    {years.map((y) => {
                      const leftPct = calculateDateOffset(
                        `${y}-01-01`,
                        bounds.minYear,
                        bounds.maxYear
                      );
                      return (
                        <div
                          key={y}
                          className="bg-border/30 absolute bottom-0 top-0 w-px"
                          style={{ left: `${leftPct}%` }}
                        />
                      );
                    })}

                    {/* Event Nodes */}
                    {group.events.map((event) => {
                      const leftPct = calculateDateOffset(
                        event.date,
                        bounds.minYear,
                        bounds.maxYear
                      );
                      const isSelected = selectedEventId === event.id;

                      return (
                        <button
                          key={event.id}
                          onClick={() => onSelectEvent(event)}
                          title={`${event.name} (${event.date}) - Click to inspect stages`}
                          className={`group absolute top-1/2 -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-transform hover:scale-110 focus:outline-none ${
                            isSelected ? 'z-20 scale-110' : 'z-10'
                          }`}
                          style={{ left: `${leftPct}%` }}
                        >
                          {/* Node Icon / Circle */}
                          <div
                            className={`flex items-center justify-center rounded-full border-2 shadow-sm ${
                              isSelected
                                ? 'ring-offset-bg-surface ring-2 ring-accent ring-offset-2'
                                : ''
                            }`}
                            style={{
                              backgroundColor: isSelected ? palette.primary : palette.light,
                              borderColor: palette.primary,
                              width: '28px',
                              height: '28px',
                            }}
                          >
                            <Calendar
                              className="h-3.5 w-3.5"
                              style={{ color: isSelected ? '#FFFFFF' : palette.primary }}
                            />
                          </div>

                          {/* Event Label Popover */}
                          <div className="bg-bg-surface/95 backdrop-blur-xs shadow-xs text-text absolute left-1/2 top-8 -translate-x-1/2 whitespace-nowrap rounded border border-border px-2 py-0.5 font-mono text-[10px] opacity-90 transition-opacity group-hover:opacity-100">
                            {event.date.slice(0, 4)}: {event.name.split(' ')[2] || event.category}
                          </div>

                          {/* Stage Markers Pill */}
                          {event.stages && event.stages.length > 0 && (
                            <div className="absolute -top-3.5 left-1/2 flex -translate-x-1/2 items-center gap-0.5">
                              {event.stages.slice(0, 5).map((st) => (
                                <span
                                  key={st.stage_id}
                                  className="h-1.5 w-1.5 rounded-full"
                                  style={{
                                    backgroundColor: st.stage_id.includes('poll')
                                      ? '#00B8D9'
                                      : palette.primary,
                                  }}
                                  title={`${st.stage_name}: ${st.date}`}
                                />
                              ))}
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="text-muted text-center text-[11px]">
        Tip: Click any event marker to inspect stage date mappings, gap days, and mini ASPI chart.
      </div>
    </div>
  );
}
