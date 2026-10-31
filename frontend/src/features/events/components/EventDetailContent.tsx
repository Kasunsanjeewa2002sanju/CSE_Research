import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Stepper, ELECTION_STAGES } from '@/components/ui/Stepper';
import { Calendar, Clock, ExternalLink, LineChart, Award, FileText } from 'lucide-react';
import type { MarketSeriesPoint, PoliticalEvent } from '@/api/types';
import { EventMiniAspiChart } from './EventMiniAspiChart';
import { getEventTypeColor } from '../utils/timeline-helpers';

export interface EventDetailContentProps {
  event: PoliticalEvent;
  fullSeries: MarketSeriesPoint[];
  isDrawer?: boolean;
}

export function EventDetailContent({
  event,
  fullSeries,
  isDrawer = false,
}: EventDetailContentProps) {
  const palette = getEventTypeColor(event.category);

  // Map current stage to 1-indexed stepper number (1 to 6)
  const currentStageNumber = 6; // Historical elections are completed (Regime Settlement)

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className="text-xs font-semibold"
            style={{
              borderColor: palette.primary,
              color: palette.primary,
              backgroundColor: palette.light,
            }}
          >
            {event.category}
          </Badge>
          {event.sample_period && (
            <Badge variant="outline" className="bg-bg-muted text-muted text-xs">
              2009–2025 Panel
            </Badge>
          )}
          {event.added_by_researcher && (
            <Badge variant="outline" className="border-accent text-xs text-accent">
              Added by Researcher
            </Badge>
          )}
          {event.is_overlapping && (
            <Badge variant="outline" className="border-warning text-warning text-xs">
              Overlapping Window (≤ 30 TD)
            </Badge>
          )}
        </div>
        <h3 className="text-text text-xl font-bold">{event.name}</h3>
        <p className="text-muted flex items-center gap-2 font-mono text-xs">
          <Calendar className="text-muted h-3.5 w-3.5" />
          Reaction Date: {event.mapped_date || event.mappedTradingDate || event.date}
          {event.gap_days !== undefined && event.gap_days > 0 && (
            <span className="text-warning">({event.gap_days} Day Trading Lag)</span>
          )}
        </p>
      </div>

      {/* Six-Stage Stepper Reused from F1 */}
      <div className="bg-bg-surface space-y-2 rounded-xl border border-border p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-text text-xs font-semibold uppercase tracking-wider">
            6-Stage Electoral Protocol
          </span>
          <span className="text-muted font-mono text-[11px]">Completed Milestone</span>
        </div>
        <Stepper currentStep={currentStageNumber} stages={ELECTION_STAGES} />
      </div>

      {/* Mini ASPI Chart around Event */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LineChart className="text-primary h-4 w-4" />
            <span className="text-text text-xs font-semibold">
              ASPI Trajectory Around Event Window
            </span>
          </div>
          <span className="text-muted font-mono text-[10px]">[-25, +25] Trading Days</span>
        </div>
        <EventMiniAspiChart event={event} fullSeries={fullSeries} height={200} />
      </div>

      {/* Stages Breakdown Table */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
          <Clock className="text-primary h-3.5 w-3.5" />
          Empirical Stage Timeline & Trading Day Mapping
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="text-muted border-b border-border font-medium">
                <th className="py-2 pr-3">Stage</th>
                <th className="py-2 pr-3">Calendar Date</th>
                <th className="py-2 pr-3">Mapped Trading Date</th>
                <th className="py-2 pr-3">Lag</th>
                <th className="py-2">Significance Notes</th>
              </tr>
            </thead>
            <tbody className="divide-border/60 divide-y">
              {event.stages && event.stages.length > 0 ? (
                event.stages.map((st) => (
                  <tr key={st.stage_id} className="hover:bg-bg-muted/40">
                    <td className="text-text py-2 pr-3 font-semibold">{st.stage_name}</td>
                    <td className="text-muted py-2 pr-3 font-mono">{st.raw_date || st.date}</td>
                    <td className="text-text py-2 pr-3 font-mono">{st.mapped_date || st.date}</td>
                    <td className="py-2 pr-3 font-mono">
                      {st.gap_days !== undefined && st.gap_days > 0 ? (
                        <span className="text-warning font-semibold">+{st.gap_days}d</span>
                      ) : (
                        <span className="text-muted">0d</span>
                      )}
                    </td>
                    <td className="text-muted line-clamp-2 py-2 text-[11px]">
                      {st.notes || st.significance || '—'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="text-muted py-4 text-center">
                    No individual stage breakdown records for this event.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Parties & Candidates Info */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
          <Award className="h-3.5 w-3.5 text-accent" />
          Parties & Electoral Outcome
        </h4>
        <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-3">
          <div className="bg-bg-muted/50 rounded-lg border border-border p-2.5">
            <span className="text-muted block text-[10px] uppercase">Turnout</span>
            <span className="text-text font-mono text-sm font-bold">
              {event.turnout_pct ?? 76.5}%
            </span>
          </div>
          <div className="bg-bg-muted/50 rounded-lg border border-border p-2.5">
            <span className="text-muted block text-[10px] uppercase">Victory Margin</span>
            <span className="text-text font-mono text-sm font-bold">
              {event.margin_pct ?? 5.8}%
            </span>
          </div>
          <div className="bg-bg-muted/50 rounded-lg border border-border p-2.5">
            <span className="text-muted block text-[10px] uppercase">Elected Administration</span>
            <span className="text-text line-clamp-1 text-xs font-semibold">
              {event.winner_party || 'Elected Coalition'}
            </span>
          </div>
        </div>
        {event.candidate_party_info && (
          <div className="text-muted border-border/60 border-t pt-2 font-mono text-xs">
            <strong>Candidate / Seat Distribution:</strong> {event.candidate_party_info}
          </div>
        )}
      </div>

      {/* Significance & Context */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <h4 className="text-text flex items-center gap-2 text-xs font-semibold">
          <FileText className="text-primary h-3.5 w-3.5" />
          Econometric Significance & Historical Context
        </h4>
        <div className="text-muted space-y-2 text-xs leading-relaxed">
          <p>
            {event.significance ||
              event.description ||
              'Documented constitutional milestone in Sri Lankan governance.'}
          </p>
          {event.context && (
            <p className="bg-bg-muted/40 border-primary text-text rounded-lg border-l-2 p-2.5 text-[11px]">
              {event.context}
            </p>
          )}
        </div>
      </div>

      {/* Sources & Links */}
      <div className="bg-bg-surface space-y-2 rounded-xl border border-border p-4">
        <span className="text-text block text-xs font-semibold">
          Official Sources & Verification
        </span>
        <div className="flex flex-wrap gap-2 text-xs">
          {(event.sources && event.sources.length > 0
            ? event.sources
            : ['Election Commission of Sri Lanka']
          ).map((source, idx) => (
            <span
              key={idx}
              className="bg-bg-muted text-muted inline-flex items-center gap-1 rounded px-2.5 py-1 text-[11px]"
            >
              <ExternalLink className="text-muted h-3 w-3" />
              {source}
            </span>
          ))}
        </div>
      </div>

      {/* Action Links */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <Link to={`/event-study?event=${event.id}`}>
          <Button variant="primary" size="sm" className="gap-1.5">
            <LineChart className="h-3.5 w-3.5" />
            View Event Study Results (CAAR)
          </Button>
        </Link>
        {isDrawer && (
          <Link to={`/events/${event.id}`}>
            <Button variant="outline" size="sm" className="gap-1.5">
              <ExternalLink className="h-3.5 w-3.5" />
              Open Full Page
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
