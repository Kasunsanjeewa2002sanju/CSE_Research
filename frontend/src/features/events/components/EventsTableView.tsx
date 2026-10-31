import { useState, useMemo } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Download, Search, CheckSquare, Square, Eye } from 'lucide-react';
import type { PoliticalEvent } from '@/api/types';
import { getEventTypeColor } from '../utils/timeline-helpers';
import { exportEventsToCsv } from '../utils/events-export';

export interface EventsTableViewProps {
  events: PoliticalEvent[];
  onSelectEvent: (event: PoliticalEvent) => void;
  selectedCompareIds: string[];
  onToggleCompare: (eventId: string) => void;
}

export function EventsTableView({
  events,
  onSelectEvent,
  selectedCompareIds,
  onToggleCompare,
}: EventsTableViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedStage, setSelectedStage] = useState('All');
  const [yearFilter, setYearFilter] = useState('All');
  const [samplePeriodOnly, setSamplePeriodOnly] = useState(false);
  const [overlappingOnly, setOverlappingOnly] = useState(false);

  // Sorting state
  const [sortField, setSortField] = useState<'date' | 'name' | 'category' | 'gap_days'>('date');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Filtered & Sorted events
  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchName = (e.name || '').toLowerCase().includes(q);
        const matchId = (e.id || '').toLowerCase().includes(q);
        const matchParty = (e.winner_party || '').toLowerCase().includes(q);
        if (!matchName && !matchId && !matchParty) return false;
      }
      if (selectedType !== 'All' && e.category.toLowerCase() !== selectedType.toLowerCase()) {
        return false;
      }
      if (selectedStage !== 'All') {
        const hasStage =
          (e.current_stage || '').toLowerCase().includes(selectedStage.toLowerCase()) ||
          (e.stages || []).some((st) =>
            st.stage_name.toLowerCase().includes(selectedStage.toLowerCase())
          );
        if (!hasStage) return false;
      }
      if (yearFilter !== 'All') {
        if (!e.date.startsWith(yearFilter)) return false;
      }
      if (samplePeriodOnly && !e.sample_period) return false;
      if (overlappingOnly && !e.is_overlapping) return false;
      return true;
    });
  }, [
    events,
    searchQuery,
    selectedType,
    selectedStage,
    yearFilter,
    samplePeriodOnly,
    overlappingOnly,
  ]);

  const sortedEvents = useMemo(() => {
    return [...filteredEvents].sort((a, b) => {
      let valA: string | number = a[sortField] ?? '';
      let valB: string | number = b[sortField] ?? '';

      if (sortField === 'date') {
        valA = a.mapped_date || a.date;
        valB = b.mapped_date || b.date;
      } else if (sortField === 'gap_days') {
        valA = a.gap_days ?? 0;
        valB = b.gap_days ?? 0;
      }

      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredEvents, sortField, sortDir]);

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters Bar */}
      <div className="bg-bg-surface space-y-3 rounded-xl border border-border p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
          {/* Search */}
          <div className="relative">
            <Search className="text-muted absolute left-2.5 top-2.5 h-3.5 w-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search election or party..."
              className="bg-bg focus:ring-primary w-full rounded-lg border border-border py-1.5 pl-8 pr-3 text-xs focus:outline-none focus:ring-1"
            />
          </div>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-bg text-text w-full rounded-lg border border-border px-2.5 py-1.5 text-xs focus:outline-none"
            aria-label="Filter by election type"
          >
            <option value="All">All Types</option>
            <option value="Presidential">Presidential</option>
            <option value="Parliamentary">Parliamentary</option>
            <option value="Provincial">Provincial</option>
          </select>

          {/* Stage Filter */}
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="bg-bg text-text w-full rounded-lg border border-border px-2.5 py-1.5 text-xs focus:outline-none"
            aria-label="Filter by stage"
          >
            <option value="All">All Stages</option>
            <option value="Announcement">Announcement</option>
            <option value="Nomination">Nomination</option>
            <option value="Polling">Polling</option>
            <option value="Result">Result</option>
            <option value="Government Formation">Government Formation</option>
          </select>

          {/* Year Filter */}
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="bg-bg text-text w-full rounded-lg border border-border px-2.5 py-1.5 text-xs focus:outline-none"
            aria-label="Filter by year"
          >
            <option value="All">All Years</option>
            {Array.from(new Set(events.map((e) => e.date.slice(0, 4))))
              .sort()
              .reverse()
              .map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
          </select>
        </div>

        {/* Flag Toggles & Export Action */}
        <div className="border-border/60 flex flex-wrap items-center justify-between gap-3 border-t pt-2">
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <label className="text-muted hover:text-text flex cursor-pointer items-center gap-1.5">
              <input
                type="checkbox"
                checked={samplePeriodOnly}
                onChange={(e) => setSamplePeriodOnly(e.target.checked)}
                className="text-primary rounded border-border focus:ring-0"
              />
              <span>Sample Period (2009–2025) Only</span>
            </label>
            <label className="text-muted hover:text-text flex cursor-pointer items-center gap-1.5">
              <input
                type="checkbox"
                checked={overlappingOnly}
                onChange={(e) => setOverlappingOnly(e.target.checked)}
                className="text-primary rounded border-border focus:ring-0"
              />
              <span>Overlapping (≤ 30 TD) Only</span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-muted font-mono text-xs">
              Showing {sortedEvents.length} of {events.length}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportEventsToCsv(sortedEvents)}
              className="h-7 gap-1.5 text-xs"
            >
              <Download className="h-3 w-3" />
              Export CSV
            </Button>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-bg-surface overflow-x-auto rounded-xl border border-border shadow-sm">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="bg-bg-muted/40 text-muted border-b border-border font-semibold">
              <th className="w-10 px-3 py-2.5 text-center" title="Select for comparison (Max 3)">
                Compare
              </th>
              <th className="cursor-pointer px-3 py-2.5" onClick={() => toggleSort('date')}>
                Reaction Date {sortField === 'date' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="cursor-pointer px-3 py-2.5" onClick={() => toggleSort('name')}>
                Event Name {sortField === 'name' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="cursor-pointer px-3 py-2.5" onClick={() => toggleSort('category')}>
                Type {sortField === 'category' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="cursor-pointer px-3 py-2.5" onClick={() => toggleSort('gap_days')}>
                Gap Lag {sortField === 'gap_days' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-3 py-2.5">Elected Administration</th>
              <th className="px-3 py-2.5">Flags</th>
              <th className="px-3 py-2.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-border/60 divide-y">
            {sortedEvents.length > 0 ? (
              sortedEvents.map((event) => {
                const palette = getEventTypeColor(event.category);
                const isChecked = selectedCompareIds.includes(event.id);

                return (
                  <tr
                    key={event.id}
                    className="hover:bg-bg-muted/50 group cursor-pointer transition-colors"
                    onClick={() => onSelectEvent(event)}
                  >
                    <td
                      className="px-3 py-2.5 text-center"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleCompare(event.id);
                      }}
                    >
                      <button
                        className="text-primary hover:text-primary-dark"
                        aria-label={`Toggle comparison for ${event.name}`}
                      >
                        {isChecked ? (
                          <CheckSquare className="h-4 w-4 text-accent" />
                        ) : (
                          <Square className="text-muted/60 h-4 w-4" />
                        )}
                      </button>
                    </td>
                    <td className="text-text px-3 py-2.5 font-mono font-medium">
                      {event.mapped_date || event.date}
                    </td>
                    <td className="text-text group-hover:text-primary px-3 py-2.5 font-semibold transition-colors">
                      {event.name}
                    </td>
                    <td className="px-3 py-2.5">
                      <Badge
                        variant="outline"
                        className="text-[10px]"
                        style={{
                          borderColor: palette.primary,
                          color: palette.primary,
                          backgroundColor: palette.light,
                        }}
                      >
                        {event.category}
                      </Badge>
                    </td>
                    <td className="px-3 py-2.5 font-mono">
                      {event.gap_days && event.gap_days > 0 ? (
                        <span className="text-warning font-semibold">+{event.gap_days}d</span>
                      ) : (
                        <span className="text-muted">0d</span>
                      )}
                    </td>
                    <td className="text-muted max-w-xs truncate px-3 py-2.5">
                      {event.winner_party || 'Elected Coalition'}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1">
                        {event.sample_period && (
                          <span
                            className="bg-primary h-2 w-2 rounded-full"
                            title="Included in 2009-2025 Walk-Forward Panel"
                          />
                        )}
                        {event.is_overlapping && (
                          <span
                            className="bg-warning h-2 w-2 rounded-full"
                            title="Overlapping event window (<= 30 TD)"
                          />
                        )}
                        {event.added_by_researcher && (
                          <span
                            className="h-2 w-2 rounded-full bg-accent"
                            title="Added by Researcher"
                          />
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-primary h-6 px-2 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEvent(event);
                        }}
                      >
                        <Eye className="mr-1 h-3 w-3" />
                        Details
                      </Button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={8} className="text-muted py-8 text-center">
                  No election events match the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
