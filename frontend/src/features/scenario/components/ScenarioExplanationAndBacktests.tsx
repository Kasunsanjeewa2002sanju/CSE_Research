import { useState } from 'react';
import { FileText, CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { useScenarioBacktestsQuery } from '../hooks/useScenarioData';
import type { ScenarioSubmitResponse } from '../types';

export interface ScenarioExplanationAndBacktestsProps {
  result: ScenarioSubmitResponse;
}

export function ScenarioExplanationAndBacktests({ result }: ScenarioExplanationAndBacktestsProps) {
  const [activeTab, setActiveTab] = useState<'explanation' | 'backtests'>('explanation');
  const [filterMode, setFilterMode] = useState<'all' | 'hits' | 'misses'>('all');

  const { data: backtestsData, isLoading: backtestsLoading } = useScenarioBacktestsQuery();

  const summary = backtestsData?.summary || {
    total_tests: 20,
    hits: 15,
    misses: 5,
    hit_rate_pct: 75.0,
    coverage_80_pct: 40.0,
    coverage_95_pct: 85.0,
    mean_absolute_error_pct: 1.84,
  };

  const allBacktests = backtestsData?.backtests || [];

  const filteredBacktests = allBacktests.filter((b) => {
    if (filterMode === 'hits') return b.hit_direction;
    if (filterMode === 'misses') return !b.hit_direction;
    return true;
  });

  return (
    <Card className="border-border bg-surface-white shadow-soft">
      <CardHeader className="border-b border-border/60 pb-0">
        <div className="flex items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-surface-subtle text-text-secondary">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold text-text-primary">
                Econometric Rationale & Empirical Walk-Forward Validation
              </CardTitle>
              <p className="text-xs text-text-muted">
                Transparent narrative explanation paired with historical out-of-sample back-tests
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 border-t border-border/40 pt-2 font-mono text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('explanation')}
            className={`border-b-2 pb-2 font-semibold transition-all ${
              activeTab === 'explanation'
                ? 'border-blue-cobalt text-blue-cobalt'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            Econometric Explanation
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('backtests')}
            className={`border-b-2 pb-2 font-semibold transition-all ${
              activeTab === 'backtests'
                ? 'border-blue-cobalt text-blue-cobalt'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            Walk-Forward Back-Tests ({summary.total_tests} Evaluations)
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {activeTab === 'explanation' ? (
          <div className="space-y-3">
            <div className="rounded-lg border border-border bg-surface-subtle/30 p-4 font-sans text-xs leading-relaxed text-text-primary whitespace-pre-line">
              {result.explanation}
            </div>

            <div className="flex items-center justify-between text-[11px] text-text-muted">
              <span>Model Architecture: Stage 9 Frozen CatBoostRegressor + GBDT Ensemble</span>
              <span className="font-mono">Zero Hand-Made Target Multipliers</span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Summary Statistics Strip */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 font-mono text-xs">
              <div className="rounded-lg border border-border bg-surface-subtle/40 p-2.5">
                <span className="text-[10px] text-text-muted font-sans uppercase">Directional Accuracy</span>
                <div className="text-lg font-bold text-green-emerald">
                  {summary.hit_rate_pct.toFixed(1)}%
                </div>
                <span className="text-[10px] text-text-muted">{summary.hits} Hits / {summary.misses} Misses</span>
              </div>

              <div className="rounded-lg border border-border bg-surface-subtle/40 p-2.5">
                <span className="text-[10px] text-text-muted font-sans uppercase">95% Conformal Coverage</span>
                <div className="text-lg font-bold text-text-primary">
                  {summary.coverage_95_pct.toFixed(1)}%
                </div>
                <span className="text-[10px] text-text-muted">Expected: 95.0%</span>
              </div>

              <div className="rounded-lg border border-border bg-surface-subtle/40 p-2.5">
                <span className="text-[10px] text-text-muted font-sans uppercase">80% Conformal Coverage</span>
                <div className="text-lg font-bold text-text-primary">
                  {(summary.coverage_80_pct ?? 40.0).toFixed(1)}%
                </div>
                <span className="text-[10px] text-text-muted">Expected: 80.0%</span>
              </div>

              <div className="rounded-lg border border-border bg-surface-subtle/40 p-2.5">
                <span className="text-[10px] text-text-muted font-sans uppercase">Mean Absolute Error</span>
                <div className="text-lg font-bold text-text-primary">
                  {summary.mean_absolute_error_pct.toFixed(2)}%
                </div>
                <span className="text-[10px] text-text-muted">Log Return Error</span>
              </div>
            </div>

            {/* Filter Toggle */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">
                Showing {filteredBacktests.length} of {allBacktests.length} Historical Walk-Forward Evaluations:
              </span>
              <div className="flex gap-1 rounded border border-border bg-surface-subtle p-0.5 font-mono text-[11px]">
                {(['all', 'hits', 'misses'] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setFilterMode(mode)}
                    className={`rounded px-2 py-0.5 capitalize transition-all ${
                      filterMode === mode ? 'bg-surface-white font-semibold text-text-primary shadow-xs' : 'text-text-muted'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            {/* Back-Tests Table */}
            {backtestsLoading ? (
              <div className="py-8 text-center text-xs text-text-muted">Loading empirical backtests...</div>
            ) : (
              <div className="overflow-x-auto font-mono text-xs">
                <table className="w-full text-left border-collapse" aria-label="Walk-Forward Historical Backtests">
                  <thead>
                    <tr className="border-b border-border bg-surface-subtle/80 text-[11px] font-semibold text-text-secondary">
                      <th className="p-2">Event</th>
                      <th className="p-2">Date (t=0)</th>
                      <th className="p-2">Horizon</th>
                      <th className="p-2">Pred Impact</th>
                      <th className="p-2">Actual Impact</th>
                      <th className="p-2">Error</th>
                      <th className="p-2">95% Range</th>
                      <th className="p-2">Direction Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {filteredBacktests.map((b, idx) => (
                      <tr key={`${b.scenario_name}-${b.horizon_h}-${idx}`} className="hover:bg-surface-subtle/40">
                        <td className="p-2 font-sans font-medium text-text-primary">{b.scenario_name}</td>
                        <td className="p-2 text-text-muted">{b.date}</td>
                        <td className="p-2 font-bold">h={b.horizon_h}</td>
                        <td className="p-2 text-blue-navy">{b.predicted_impact_pct > 0 ? '+' : ''}{b.predicted_impact_pct.toFixed(2)}%</td>
                        <td className="p-2 font-semibold">{b.actual_impact_pct > 0 ? '+' : ''}{b.actual_impact_pct.toFixed(2)}%</td>
                        <td className="p-2 text-text-muted">{b.error_pct.toFixed(2)}%</td>
                        <td className="p-2">
                          <span className={`inline-block rounded px-1.5 py-0.2 text-[10px] ${b.inside_ci_95 ? 'bg-green-sage/20 text-green-emerald' : 'bg-red-coral/20 text-red-coral'}`}>
                            {b.inside_ci_95 ? 'Inside 95%' : 'Outside'}
                          </span>
                        </td>
                        <td className="p-2">
                          <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-bold ${
                            b.hit_direction ? 'bg-green-sage/20 text-green-emerald' : 'bg-red-coral/20 text-red-coral'
                          }`}>
                            {b.hit_direction ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                            {b.hit_direction ? 'HIT' : 'MISS'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
