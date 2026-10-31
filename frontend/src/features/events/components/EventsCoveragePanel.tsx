import { Badge } from '@/components/ui/Badge';
import { Layers, ShieldAlert, Calendar, Bookmark } from 'lucide-react';
import type { EventsCoverage } from '@/api/types';
import { getEventTypeColor } from '../utils/timeline-helpers';

export interface EventsCoveragePanelProps {
  coverage?: EventsCoverage;
  isLoading?: boolean;
}

export function EventsCoveragePanel({ coverage, isLoading }: EventsCoveragePanelProps) {
  if (isLoading || !coverage) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-bg-muted/40 h-32 animate-pulse rounded-xl border border-border"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards Strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">Total Events</span>
          <span className="text-text font-mono text-xl font-bold">{coverage.total_events}</span>
          <span className="text-muted mt-0.5 block text-[10px]">Elections (2000–2024)</span>
        </div>

        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">Total Stages</span>
          <span className="text-primary font-mono text-xl font-bold">{coverage.total_stages}</span>
          <span className="text-muted mt-0.5 block text-[10px]">Stage-level mappings</span>
        </div>

        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">Coverage Span</span>
          <span className="text-text font-mono text-xl font-bold">{coverage.years_covered}</span>
          <span className="text-muted mt-0.5 block text-[10px]">25 calendar years</span>
        </div>

        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">Sample Period</span>
          <span className="font-mono text-xl font-bold text-accent">
            {coverage.sample_period_events}
          </span>
          <span className="text-muted mt-0.5 block text-[10px]">2009–2025 Panel</span>
        </div>

        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">
            Overlapping Events
          </span>
          <span className="text-warning font-mono text-xl font-bold">
            {coverage.overlapping_events}
          </span>
          <span className="text-muted mt-0.5 block text-[10px]">≤ 30 Trading Days</span>
        </div>

        <div className="bg-bg-surface rounded-xl border border-border p-3">
          <span className="text-muted block font-mono text-[10px] uppercase">
            Added by Researcher
          </span>
          <span className="text-text font-mono text-xl font-bold">
            {coverage.added_by_researcher_events}
          </span>
          <span className="text-muted mt-0.5 block text-[10px]">Manual annotations</span>
        </div>
      </div>

      {/* Breakdowns: By Type and By Stage */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Type Breakdown */}
        <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
          <div className="border-border/80 flex items-center justify-between border-b pb-2">
            <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
              <Layers className="text-primary h-4 w-4" />
              Event Breakdown by Constitutional Type
            </h4>
            <span className="text-muted font-mono text-[11px]">{coverage.total_events} Total</span>
          </div>

          <div className="space-y-3">
            {Object.entries(coverage.counts_by_type).map(([type, count]) => {
              const palette = getEventTypeColor(type);
              const pct = Math.round((count / coverage.total_events) * 100);

              return (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text font-semibold">{type} Elections</span>
                    <span className="text-muted font-mono">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="bg-bg-muted h-2 w-full overflow-hidden rounded-full">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{ width: `${pct}%`, backgroundColor: palette.primary }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stage Breakdown */}
        <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
          <div className="border-border/80 flex items-center justify-between border-b pb-2">
            <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
              <Calendar className="h-4 w-4 text-accent" />
              Stage-Level Observation Counts
            </h4>
            <span className="text-muted font-mono text-[11px]">{coverage.total_stages} Total</span>
          </div>

          <div className="space-y-2">
            {Object.entries(coverage.counts_by_stage).map(([stage, count]) => (
              <div
                key={stage}
                className="bg-bg-muted/40 flex items-center justify-between rounded-lg p-2 text-xs"
              >
                <span className="text-text font-medium">{stage}</span>
                <span className="text-primary font-mono font-semibold">{count} stages</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Uncovered / Excluded Types Reported by API Taxonomy */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <div className="border-border/80 flex items-center justify-between border-b pb-2">
          <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
            <ShieldAlert className="text-muted h-4 w-4" />
            Platform Taxonomy Scope & Excluded Event Types
          </h4>
          <span className="text-muted font-mono text-[10px]">Reported by Backend Taxonomy</span>
        </div>

        <p className="text-muted text-xs leading-relaxed">
          The following event categories are defined in the research platform's taxonomy (`/meta`),
          but are excluded or isolated from the constitutional election event catalog:
        </p>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {coverage.uncovered_types.map((uncovered) => (
            <div
              key={uncovered.type}
              className="border-border/70 bg-bg-muted/30 space-y-1 rounded-lg border p-3"
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-muted border-border text-[10px]">
                  {uncovered.type} (0 Events)
                </Badge>
                <span className="text-text text-xs font-semibold">
                  {uncovered.type} Regime Shocks
                </span>
              </div>
              <p className="text-muted text-[11px] leading-normal">{uncovered.reason}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Researcher Attribution & Honest UI Disclaimer */}
      <div className="bg-bg-muted/40 text-muted flex items-start gap-2 rounded-lg border border-border p-3 text-[11px]">
        <Bookmark className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
        <div>
          <strong>Rule FR5 (Honest UI & Provenance):</strong> All 24 events are sourced from the
          Election Commission of Sri Lanka and the Parliament of Sri Lanka Handbook. Any manual
          additions or date alignments performed by the research team are flagged with the{' '}
          <span className="font-semibold text-accent">"Added by Researcher"</span> badge.
        </div>
      </div>
    </div>
  );
}
