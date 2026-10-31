import { Button } from '@/components/ui/Button';
import { Download, Search } from 'lucide-react';
import type {
  ModelFamilyFilter,
  HorizonFilter,
  FeatureSetFilter,
  MetricSortField,
} from '../types';

export interface LeaderboardFiltersProps {
  familyFilter: ModelFamilyFilter;
  onFamilyFilterChange: (f: ModelFamilyFilter) => void;
  horizonFilter: HorizonFilter;
  onHorizonFilterChange: (h: HorizonFilter) => void;
  featureSetFilter: FeatureSetFilter;
  onFeatureSetFilterChange: (fs: FeatureSetFilter) => void;
  selectedMetric: MetricSortField;
  onMetricChange: (m: MetricSortField) => void;
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  onlySignificant: boolean;
  onOnlySignificantChange: (sig: boolean) => void;
  filteredCount: number;
  onExportCSV: () => void;
}

export function LeaderboardFilters({
  familyFilter,
  onFamilyFilterChange,
  horizonFilter,
  onHorizonFilterChange,
  featureSetFilter,
  onFeatureSetFilterChange,
  selectedMetric,
  onMetricChange,
  searchQuery,
  onSearchQueryChange,
  onlySignificant,
  onOnlySignificantChange,
  filteredCount,
  onExportCSV,
}: LeaderboardFiltersProps) {
  return (
    <div className="space-y-3">
      {/* Search, Metric Selector & CSV Export */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          {/* Search Input */}
          <div className="relative min-w-[200px] flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              placeholder="Search model, family..."
              className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
          </div>

          {/* Metric Selector */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-muted-foreground font-medium">Metric:</span>
            <select
              value={selectedMetric}
              onChange={(e) => onMetricChange(e.target.value as MetricSortField)}
              className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground font-medium focus:border-primary focus:outline-none"
              aria-label="Select ranking metric"
            >
              <option value="directional_accuracy">Directional Accuracy (%)</option>
              <option value="oos_r2">Out-of-Sample R²</option>
              <option value="balanced_accuracy">Balanced Accuracy (%)</option>
              <option value="rmse">RMSE (Lower Better)</option>
              <option value="mae">MAE (Lower Better)</option>
              <option value="theils_u">Theil's U (Lower Better)</option>
              <option value="training_time_s">Training Time (s)</option>
            </select>
          </div>
        </div>

        <Button size="sm" variant="outline" onClick={onExportCSV} className="text-xs h-8 self-start sm:self-auto">
          <Download className="w-3.5 h-3.5 mr-1.5" /> Export Filtered CSV ({filteredCount})
        </Button>
      </div>

      {/* Filter Chips Bar */}
      <div className="flex flex-wrap items-center gap-3 border-y border-border/60 py-2.5 text-xs">
        {/* Family Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground font-medium">Family:</span>
          {(['all', 'shallow', 'deep', 'foundation', 'statistical', 'baseline'] as ModelFamilyFilter[]).map((fam) => (
            <button
              key={fam}
              onClick={() => onFamilyFilterChange(fam)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                familyFilter === fam
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'bg-muted/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {fam === 'all' ? 'All' : fam.charAt(0).toUpperCase() + fam.slice(1)}
            </button>
          ))}
        </div>

        {/* Horizon Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground font-medium">Horizon:</span>
          {(['all', '1', '5'] as HorizonFilter[]).map((h) => (
            <button
              key={h}
              onClick={() => onHorizonFilterChange(h)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                horizonFilter === h
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'bg-muted/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {h === 'all' ? 'All' : `h=${h}`}
            </button>
          ))}
        </div>

        {/* Feature Set Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground font-medium">Feature Set:</span>
          {(['all', 'A', 'B', 'C'] as FeatureSetFilter[]).map((fs) => (
            <button
              key={fs}
              onClick={() => onFeatureSetFilterChange(fs)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                featureSetFilter === fs
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'bg-muted/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {fs === 'all' ? 'All' : `Set ${fs}`}
            </button>
          ))}
        </div>

        {/* Only Significant Toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer ml-auto text-[11px] text-muted-foreground select-none">
          <input
            type="checkbox"
            checked={onlySignificant}
            onChange={(e) => onOnlySignificantChange(e.target.checked)}
            className="rounded border-border text-primary focus:ring-0"
          />
          <span>FDR Significant Only</span>
        </label>
      </div>
    </div>
  );
}
