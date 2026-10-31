import { Search, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import type { NewsFilters as ApiNewsFilters } from '../types';

export interface NewsFiltersState {
  source: string;
  category: string;
  stage: string;
  relevance: string;
  language: string;
  evidenceStrength: string;
  search: string;
  fromDate: string;
  toDate: string;
}
 
export interface NewsFiltersProps {
  filtersState: NewsFiltersState;
  onChange: (key: keyof NewsFiltersState, value: string) => void;
  onReset: () => void;
  apiFilterOptions?: ApiNewsFilters;
  totalResults?: number;
}

export function NewsFilters({
  filtersState,
  onChange,
  onReset,
  apiFilterOptions,
  totalResults,
}: NewsFiltersProps) {
  const sources = apiFilterOptions?.sources || [];
  const categories = apiFilterOptions?.categories || [];
  const stages = apiFilterOptions?.stages || [];
  const languages = apiFilterOptions?.languages || [];
  const evidenceStrengths = apiFilterOptions?.evidence_strengths || ['all', 'weak', 'moderate', 'strong'];
  const relevanceOptions = apiFilterOptions?.relevance_options || ['all', 'relevant', 'not_relevant'];

  const hasActiveFilters =
    filtersState.source !== 'all' ||
    filtersState.category !== 'all' ||
    filtersState.stage !== 'all' ||
    filtersState.relevance !== 'all' ||
    filtersState.language !== 'all' ||
    filtersState.evidenceStrength !== 'all' ||
    filtersState.search.trim() !== '' ||
    filtersState.fromDate !== '' ||
    filtersState.toDate !== '';

  return (
    <div className="space-y-3 rounded-card border border-border bg-surface-white p-4 shadow-card">
      {/* Top Search & Results row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" aria-hidden="true" />
          <input
            type="search"
            value={filtersState.search}
            onChange={(e) => onChange('search', e.target.value)}
            placeholder="Search headline, entity, or macroeconomic keywords..."
            className="w-full rounded-button border border-border bg-background py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:bg-surface-white focus:outline-none focus:ring-1 focus:ring-accent"
            aria-label="Search news"
          />
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {totalResults !== undefined && (
            <span className="font-mono text-xs font-semibold text-text-muted whitespace-nowrap">
              {totalResults.toLocaleString()} items matched
            </span>
          )}
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="flex items-center gap-1.5 text-xs shrink-0"
            >
              <RotateCcw className="h-3.5 w-3.5 text-text-muted" />
              <span>Reset</span>
            </Button>
          )}
        </div>
      </div>

      {/* Primary Filter Selectors Grid */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
        {/* Source Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-source" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Source
          </label>
          <select
            id="filter-source"
            value={filtersState.source}
            onChange={(e) => onChange('source', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Category Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-cat" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Category
          </label>
          <select
            id="filter-cat"
            value={filtersState.category}
            onChange={(e) => onChange('category', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Stage Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-stage" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Stage
          </label>
          <select
            id="filter-stage"
            value={filtersState.stage}
            onChange={(e) => onChange('stage', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Stages</option>
            {stages.map((st) => (
              <option key={st} value={st}>
                {st.replace(/_/g, ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Relevance Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-rel" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Relevance
          </label>
          <select
            id="filter-rel"
            value={filtersState.relevance}
            onChange={(e) => onChange('relevance', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            {relevanceOptions.map((r) => (
              <option key={r} value={r}>
                {r === 'all'
                  ? 'All Relevance'
                  : r === 'relevant'
                  ? 'Macro Relevant'
                  : 'Not Relevant'}
              </option>
            ))}
          </select>
        </div>

        {/* Language Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-lang" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Language
          </label>
          <select
            id="filter-lang"
            value={filtersState.language}
            onChange={(e) => onChange('language', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Languages</option>
            {languages.map((l) => (
              <option key={l} value={l}>
                {l === 'en' ? 'English (EN)' : l === 'si' ? 'Sinhala (SI)' : l === 'ta' ? 'Tamil (TA)' : l.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Evidence Strength Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-ev" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            Evidence
          </label>
          <select
            id="filter-ev"
            value={filtersState.evidenceStrength}
            onChange={(e) => onChange('evidenceStrength', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            {evidenceStrengths.map((ev) => (
              <option key={ev} value={ev}>
                {ev === 'all' ? 'All Strengths' : `${ev.charAt(0).toUpperCase() + ev.slice(1)} Evidence`}
              </option>
            ))}
          </select>
        </div>

        {/* From Date Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-from" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            From Date
          </label>
          <input
            type="date"
            id="filter-from"
            value={filtersState.fromDate}
            onChange={(e) => onChange('fromDate', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        {/* To Date Filter */}
        <div className="flex flex-col gap-1 min-w-0">
          <label htmlFor="filter-to" className="text-[11px] font-semibold uppercase tracking-wider text-text-muted truncate">
            To Date
          </label>
          <input
            type="date"
            id="filter-to"
            value={filtersState.toDate}
            onChange={(e) => onChange('toDate', e.target.value)}
            className="w-full rounded border border-border bg-surface-white px-2 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>
    </div>
  );
}
export default NewsFilters;
