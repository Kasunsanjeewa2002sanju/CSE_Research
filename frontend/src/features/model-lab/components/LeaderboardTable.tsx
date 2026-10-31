import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, Trophy, HelpCircle, ArrowUpDown } from 'lucide-react';
import type {
  ModelLeaderboardItem,
  ModelFamilyFilter,
  HorizonFilter,
  FeatureSetFilter,
  MetricSortField,
} from '../types';
import { LeaderboardFilters } from './LeaderboardFilters';

export interface LeaderboardTableProps {
  models: ModelLeaderboardItem[];
  selectedMetric: MetricSortField;
  onMetricChange: (metric: MetricSortField) => void;
}

export function LeaderboardTable({ models, selectedMetric, onMetricChange }: LeaderboardTableProps) {
  const [familyFilter, setFamilyFilter] = useState<ModelFamilyFilter>('all');
  const [horizonFilter, setHorizonFilter] = useState<HorizonFilter>('all');
  const [featureSetFilter, setFeatureSetFilter] = useState<FeatureSetFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortAsc, setSortAsc] = useState(false);
  const [onlySignificant, setOnlySignificant] = useState(false);

  // Filtered & sorted models
  const filteredModels = useMemo(() => {
    return models
      .filter((m) => {
        if (familyFilter !== 'all' && m.family !== familyFilter) return false;
        if (horizonFilter !== 'all' && m.horizon !== Number(horizonFilter)) return false;
        if (featureSetFilter !== 'all' && !m.feature_set.includes(featureSetFilter)) return false;
        if (onlySignificant && !m.significantly_better_than_baseline && !m.is_baseline) return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchName = m.model_name.toLowerCase().includes(q);
          const matchFam = m.family.toLowerCase().includes(q);
          const matchSet = m.feature_set.toLowerCase().includes(q);
          if (!matchName && !matchFam && !matchSet) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let valA = 0;
        let valB = 0;
        if (selectedMetric === 'oos_r2') {
          valA = a.oos_r2_mean;
          valB = b.oos_r2_mean;
        } else if (selectedMetric === 'directional_accuracy') {
          valA = a.accuracy_mean;
          valB = b.accuracy_mean;
        } else if (selectedMetric === 'balanced_accuracy') {
          valA = a.balanced_accuracy_mean;
          valB = b.balanced_accuracy_mean;
        } else if (selectedMetric === 'rmse') {
          valA = a.rmse_mean;
          valB = b.rmse_mean;
        } else if (selectedMetric === 'mae') {
          valA = a.mae_mean;
          valB = b.mae_mean;
        } else if (selectedMetric === 'theils_u') {
          valA = a.theils_u_mean;
          valB = b.theils_u_mean;
        } else if (selectedMetric === 'training_time_s') {
          valA = a.training_time_s;
          valB = b.training_time_s;
        }

        const isLowerBetter = selectedMetric === 'rmse' || selectedMetric === 'mae' || selectedMetric === 'theils_u' || selectedMetric === 'training_time_s';
        const mult = (sortAsc ? 1 : -1) * (isLowerBetter ? -1 : 1);
        return (valA - valB) * mult;
      });
  }, [models, familyFilter, horizonFilter, featureSetFilter, onlySignificant, searchQuery, selectedMetric, sortAsc]);

  // Export filtered models as CSV
  const handleExportCSV = () => {
    const headers = [
      'Model ID', 'Model Name', 'Family', 'Horizon', 'Feature Set', 'Is Champion',
      'Is Baseline', 'OOS R2 Mean', 'OOS R2 SD', 'Directional Accuracy Mean',
      'Directional Accuracy SD', 'Balanced Accuracy Mean', 'RMSE Mean', 'MAE Mean',
      'Theil U Mean', 'Runtime (s)', 'Significantly Better Than Baseline', 'Correction Method',
    ];

    const rows = filteredModels.map((m) => [
      m.model_id, `"${m.model_name}"`, m.family, m.horizon, `"${m.feature_set}"`,
      m.is_champion, m.is_baseline, m.oos_r2_mean, m.oos_r2_std, m.accuracy_mean,
      m.accuracy_std, m.balanced_accuracy_mean, m.rmse_mean, m.mae_mean,
      m.theils_u_mean, m.training_time_s, m.significantly_better_than_baseline,
      `"${m.significance_correction_method}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csvContent));
    link.setAttribute('download', `cse_models_leaderboard_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-card rounded-lg border border-border p-5 shadow-sm space-y-4">
      {/* Table Header & Controls Bar */}
      <div>
        <h3 className="font-heading text-base font-bold text-foreground">
          Empirical Walk-Forward Model Leaderboard
        </h3>
        <p className="text-muted-foreground text-xs font-sans">
          Phase-level means and standard deviations across 5 non-overlapping purged walk-forward eras (1994–2025).
        </p>
      </div>

      {/* Extracted Filter Controls Component */}
      <LeaderboardFilters
        familyFilter={familyFilter}
        onFamilyFilterChange={setFamilyFilter}
        horizonFilter={horizonFilter}
        onHorizonFilterChange={setHorizonFilter}
        featureSetFilter={featureSetFilter}
        onFeatureSetFilterChange={setFeatureSetFilter}
        selectedMetric={selectedMetric}
        onMetricChange={onMetricChange}
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        onlySignificant={onlySignificant}
        onOnlySignificantChange={setOnlySignificant}
        filteredCount={filteredModels.length}
        onExportCSV={handleExportCSV}
      />

      {/* Table Render */}
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full text-left text-xs font-sans">
          <thead className="bg-muted/50 text-[11px] font-semibold text-muted-foreground uppercase border-b border-border">
            <tr>
              <th className="px-3 py-2.5">Rank</th>
              <th className="px-3 py-2.5">Model / Architecture</th>
              <th className="px-3 py-2.5">Family</th>
              <th className="px-3 py-2.5">Horizon</th>
              <th className="px-3 py-2.5">Feature Set</th>
              <th className="px-3 py-2.5 cursor-pointer select-none" onClick={() => setSortAsc(!sortAsc)}>
                <div className="flex items-center gap-1">
                  <span>Selected Metric ({selectedMetric})</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="px-3 py-2.5">OOS R² (Mean ± SD)</th>
              <th className="px-3 py-2.5">Dir. Acc (Mean ± SD)</th>
              <th className="px-3 py-2.5">RMSE (Mean ± SD)</th>
              <th className="px-3 py-2.5">Status &amp; Tests</th>
              <th className="px-3 py-2.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {filteredModels.map((m, idx) => {
              const isBaseline = m.is_baseline;
              const isChamp = m.is_champion;
              return (
                <tr
                  key={m.model_id}
                  className={`transition-colors ${
                    isChamp
                      ? 'bg-blue-50/70 dark:bg-blue-950/30 hover:bg-blue-100/50 dark:hover:bg-blue-900/40'
                      : isBaseline
                        ? 'bg-amber-50/50 dark:bg-amber-950/20 hover:bg-amber-100/40 dark:hover:bg-amber-900/30'
                        : 'hover:bg-muted/40'
                  }`}
                >
                  <td className="px-3 py-2.5 font-mono text-muted-foreground">
                    {isChamp ? <Trophy className="h-4 w-4 text-amber-500 inline" /> : `#${idx + 1}`}
                  </td>
                  <td className="px-3 py-2.5 font-medium text-foreground">
                    <div className="flex items-center gap-1.5">
                      <Link
                        to={`/models/${m.model_id}`}
                        className="hover:text-primary hover:underline font-semibold"
                      >
                        {m.model_name}
                      </Link>
                      {isChamp && (
                        <Badge variant="outline" className="text-[10px] border-amber-500 text-amber-700 dark:text-amber-300">
                          Champion
                        </Badge>
                      )}
                      {isBaseline && (
                        <Badge variant="outline" className="text-[10px] border-amber-600/60 text-amber-800 dark:text-amber-400">
                          Baseline
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2.5 capitalize text-muted-foreground">{m.family}</td>
                  <td className="px-3 py-2.5 font-mono">h={m.horizon}</td>
                  <td className="px-3 py-2.5">{m.feature_set}</td>
                  <td className="px-3 py-2.5 font-mono font-semibold text-foreground">
                    {selectedMetric === 'oos_r2' && `${m.oos_r2_mean.toFixed(4)} ± ${m.oos_r2_std.toFixed(4)}`}
                    {selectedMetric === 'directional_accuracy' && `${m.accuracy_mean.toFixed(2)}% ± ${m.accuracy_std.toFixed(2)}%`}
                    {selectedMetric === 'balanced_accuracy' && `${m.balanced_accuracy_mean.toFixed(2)}%`}
                    {selectedMetric === 'rmse' && `${m.rmse_mean.toFixed(4)} ± ${m.rmse_std.toFixed(4)}`}
                    {selectedMetric === 'mae' && `${m.mae_mean.toFixed(4)} ± ${m.mae_std.toFixed(4)}`}
                    {selectedMetric === 'theils_u' && `${m.theils_u_mean.toFixed(3)}`}
                    {selectedMetric === 'training_time_s' && `${m.training_time_s}s`}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-muted-foreground">
                    {m.oos_r2_mean.toFixed(4)} <span className="text-[10px]">±{m.oos_r2_std.toFixed(4)}</span>
                  </td>
                  <td className="px-3 py-2.5 font-mono text-muted-foreground">
                    {m.accuracy_mean.toFixed(1)}% <span className="text-[10px]">±{m.accuracy_std.toFixed(1)}%</span>
                  </td>
                  <td className="px-3 py-2.5 font-mono text-muted-foreground">
                    {m.rmse_mean.toFixed(4)}
                  </td>
                  <td className="px-3 py-2.5">
                    {m.significantly_better_than_baseline ? (
                      <Badge variant="outline" className="gap-1 border-teal-500 text-teal-700 dark:text-teal-300 text-[10px] whitespace-nowrap">
                        <CheckCircle2 className="h-3 w-3 text-teal-600 dark:text-teal-400" />
                        <span>Sig. &gt; Baseline ({m.significance_correction_method})</span>
                      </Badge>
                    ) : isBaseline ? (
                      <span className="text-[11px] text-amber-700 dark:text-amber-400 font-mono">Benchmark Reference</span>
                    ) : (
                      <span className="text-[11px] text-muted-foreground font-mono">Not Sig. (p &ge; 0.05)</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right whitespace-nowrap">
                    <Link
                      to={`/models/${m.model_id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline"
                    >
                      <HelpCircle className="h-3 w-3" /> Diagnostics
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
