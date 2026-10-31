import React, { useState, useMemo } from 'react';
import type {
  FeatureDictionaryItem,
  PhaseEventCoverageItem,
  FeatureSetFilter,
  FeatureGroupFilter,
} from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface FeatureDictionaryProps {
  features: FeatureDictionaryItem[];
  phaseCoverage?: PhaseEventCoverageItem[];
}

export const FeatureDictionary: React.FC<FeatureDictionaryProps> = ({
  features,
  phaseCoverage = [],
}) => {
  const [setFilter, setSetFilter] = useState<FeatureSetFilter>('all');
  const [groupFilter, setGroupFilter] = useState<FeatureGroupFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filter features based on Set, Group, and Search query
  const filteredFeatures = useMemo(() => {
    return features.filter((feat) => {
      // 1. Feature Set filter
      if (setFilter !== 'all') {
        const sets = feat.feature_sets ?? [];
        if (!sets.includes(setFilter)) {
          return false;
        }
      }

      // 2. Group filter
      if (groupFilter !== 'all' && feat.group !== groupFilter) {
        return false;
      }

      // 3. Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = feat.feature_name.toLowerCase().includes(query);
        const matchesDesc = feat.description.toLowerCase().includes(query);
        const matchesAvail = (feat.availability ?? '').toLowerCase().includes(query);
        const matchesCat = feat.category.toLowerCase().includes(query);
        if (!matchesName && !matchesDesc && !matchesAvail && !matchesCat) {
          return false;
        }
      }

      return true;
    });
  }, [features, setFilter, groupFilter, searchQuery]);

  // Pagination slice
  const totalPages = Math.ceil(filteredFeatures.length / pageSize) || 1;
  const pagedFeatures = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredFeatures.slice(start, start + pageSize);
  }, [filteredFeatures, page, pageSize]);

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div>
        <h2 className="text-foreground text-xl font-bold tracking-tight">
          Feature Sets Dictionary & Temporal Availability
        </h2>
        <p className="text-muted-foreground text-sm">
          Complete catalog of engineered causal features across Feature Sets A (Price/Technical), B
          (Market Activity), and C (Electoral Cycle & Prior CAR).
        </p>
      </div>

      {/* 2. Interactive Filter Controls */}
      <Card padding="md">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Feature Set Selector Chips */}
            <div
              className="flex flex-wrap items-center gap-1.5"
              role="tablist"
              aria-label="Feature Set Filter"
            >
              <span className="text-muted-foreground mr-1 text-xs font-semibold">Feature Set:</span>
              {(['all', 'A', 'B', 'C'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => {
                    setSetFilter(s);
                    setPage(1);
                  }}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                    setFilter === s
                      ? 'bg-primary text-white shadow-sm'
                      : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                  role="tab"
                  aria-selected={setFilter === s}
                >
                  {s === 'all'
                    ? 'All Sets (57)'
                    : `Set ${s} (${s === 'A' ? 24 : s === 'B' ? 34 : 57})`}
                </button>
              ))}
            </div>

            {/* Group Filter Chips */}
            <div
              className="flex flex-wrap items-center gap-1.5"
              role="tablist"
              aria-label="Group Filter"
            >
              <span className="text-muted-foreground mr-1 text-xs font-semibold">Group:</span>
              {(['all', 'price', 'activity', 'event'] as const).map((g) => (
                <button
                  key={g}
                  onClick={() => {
                    setGroupFilter(g);
                    setPage(1);
                  }}
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize transition-all ${
                    groupFilter === g
                      ? 'bg-accent text-white shadow-sm'
                      : 'bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                  role="tab"
                  aria-selected={groupFilter === g}
                >
                  {g === 'all' ? 'All Groups' : g}
                </button>
              ))}
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search by feature name, definition, category, or availability..."
              value={searchQuery}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              aria-label="Search feature dictionary"
            />
          </div>
        </div>
      </Card>

      {/* 3. Feature Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              Feature Dictionary ({filteredFeatures.length} matching)
            </CardTitle>
            <span className="text-muted-foreground font-mono text-xs">
              Showing {Math.min(filteredFeatures.length, (page - 1) * pageSize + 1)}–
              {Math.min(filteredFeatures.length, page * pageSize)} of {filteredFeatures.length}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-xs"
              role="table"
              aria-label="Engineered Feature Dictionary Table"
            >
              <thead>
                <tr className="bg-muted/40 text-muted-foreground border-b border-border font-semibold">
                  <th className="p-3">Feature Name</th>
                  <th className="p-3">Sets</th>
                  <th className="p-3">Group / Category</th>
                  <th className="p-3">Definition</th>
                  <th className="p-3">Availability & Restrictions</th>
                  <th className="p-3">Stationarity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pagedFeatures.map((feat) => (
                  <tr key={feat.feature_name} className="hover:bg-muted/20">
                    <td className="text-primary p-3 font-mono font-bold">{feat.feature_name}</td>
                    <td className="p-3">
                      <div className="flex gap-1">
                        {(feat.feature_sets ?? ['A', 'B', 'C']).map((s) => (
                          <span
                            key={s}
                            className="bg-primary/10 text-primary inline-block rounded px-1.5 py-0.5 font-mono text-[10px] font-bold"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge variant="outline" className="text-[10px] capitalize">
                        {feat.group || feat.category}
                      </Badge>
                    </td>
                    <td className="text-foreground/90 max-w-sm p-3">{feat.description}</td>
                    <td className="text-muted-foreground max-w-xs p-3 font-mono text-[11px]">
                      {feat.availability || 'Full 30-year panel'}
                    </td>
                    <td className="p-3 font-mono text-[11px] text-teal-600 dark:text-teal-400">
                      {feat.stationarity ? 'I(0) Stationary' : 'Non-Stationary'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="border-border/60 mt-4 flex items-center justify-between border-t pt-3 text-xs">
              <span className="text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 4. Coverage by Phase Table (Validation Days inside Event Windows) */}
      {phaseCoverage.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle className="text-base">
                  Event Window Coverage by Walk-Forward Validation Phase
                </CardTitle>
                <p className="text-muted-foreground text-xs">
                  Proportion of out-of-sample validation trading days falling within active election
                  stages and post-event windows.
                </p>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                Stage 5 Audit
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table
                className="w-full text-left text-xs"
                role="table"
                aria-label="Event Window Coverage by Phase Table"
              >
                <thead>
                  <tr className="bg-muted/40 text-muted-foreground border-b border-border font-semibold">
                    <th className="p-3">Phase</th>
                    <th className="p-3">Validation Dates</th>
                    <th className="p-3 text-right">Val Days Total</th>
                    <th className="p-3 text-right">In Active Stage</th>
                    <th className="p-3 text-right">% in Active Stage</th>
                    <th className="p-3 text-right">Window [0, +2]</th>
                    <th className="p-3 text-right">Window [0, +7]</th>
                    <th className="p-3 text-right">Window [0, +15]</th>
                    <th className="p-3 text-right">Window [0, +30]</th>
                    <th className="p-3 text-right">% in Window [0, +30]</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {phaseCoverage.map((row) => (
                    <tr key={row.phase} className="hover:bg-muted/20">
                      <td className="text-primary p-3 font-bold">{row.phase}</td>
                      <td className="p-3 font-sans">{row.val_dates}</td>
                      <td className="p-3 text-right font-medium">{row.val_days_total} TD</td>
                      <td className="p-3 text-right">{row.days_in_active_stage} TD</td>
                      <td className="text-primary p-3 text-right font-semibold">
                        {row.pct_in_active_stage}
                      </td>
                      <td className="text-muted-foreground p-3 text-right">
                        {row.days_in_win_0_2}
                      </td>
                      <td className="text-muted-foreground p-3 text-right">
                        {row.days_in_win_0_7}
                      </td>
                      <td className="text-muted-foreground p-3 text-right">
                        {row.days_in_win_0_15}
                      </td>
                      <td className="p-3 text-right font-bold text-cyan-600 dark:text-cyan-400">
                        {row.days_in_win_0_30}
                      </td>
                      <td className="p-3 text-right font-bold text-cyan-600 dark:text-cyan-400">
                        {row.pct_in_win_0_30}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-muted-foreground mt-3 text-[11px] italic">
              Note: Phase 4 (2021-01-04 to 2023-12-29) reports 0.0% coverage because no national
              elections were held during the COVID-19 pandemic and acute macroeconomic crisis until
              the September 2024 presidential election in Phase 5.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
