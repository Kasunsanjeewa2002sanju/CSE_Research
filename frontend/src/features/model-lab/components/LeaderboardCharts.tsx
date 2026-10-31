import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { BarChart2, Grid, Target, TrendingUp, Zap, Table as TableIcon } from 'lucide-react';
import type { ModelLeaderboardItem, MetricSortField, SummaryChartTab } from '../types';
import {
  FAMILY_COLORS,
  BarErrorPlot,
  PhaseHeatmapPlot,
  DirectionDotPlot,
  OosR2DotPlot,
  RuntimeScatterPlot,
} from './LeaderboardChartPlots';

export interface LeaderboardChartsProps {
  models: ModelLeaderboardItem[];
  selectedMetric: MetricSortField;
  summaryMessage?: string;
  anyModelBeatsBaseline?: boolean;
}

export function LeaderboardCharts({
  models,
  selectedMetric,
  summaryMessage,
  anyModelBeatsBaseline = true,
}: LeaderboardChartsProps) {
  const [activeTab, setActiveTab] = useState<SummaryChartTab>('metric_bars');
  const [showTableAlt, setShowTableAlt] = useState(false);

  // Take top 8 non-baseline models + baselines for clean visual density
  const chartModels = useMemo(() => {
    const nonBaselines = models.filter((m) => !m.is_baseline).slice(0, 8);
    const baselines = models.filter((m) => m.is_baseline);
    return [...nonBaselines, ...baselines];
  }, [models]);

  const tabs: { id: SummaryChartTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'metric_bars', label: 'Metric by Model (±1 SD)', icon: BarChart2 },
    { id: 'phase_heatmap', label: 'Phase × Model Heatmap', icon: Grid },
    { id: 'direction_accuracy', label: 'Directional Accuracy (95% CI)', icon: Target },
    { id: 'oos_r2', label: 'Out-of-Sample R²', icon: TrendingUp },
    { id: 'runtime_scatter', label: 'Accuracy vs Runtime', icon: Zap },
  ];

  return (
    <div className="space-y-4">
      {/* Prominent Baseline Status Banner */}
      {!anyModelBeatsBaseline ? (
        <div className="p-4 rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 text-sm">
          <strong>Baseline Comparison Result:</strong>{' '}
          {summaryMessage || 'No model significantly beats the prevailing historical mean baseline after multiple testing correction.'}
        </div>
      ) : (
        <div className="p-3.5 rounded-xl border border-teal-200 dark:border-teal-800 bg-teal-50/70 dark:bg-teal-950/30 text-teal-900 dark:text-teal-200 text-xs flex items-center justify-between">
          <div>
            <span className="font-semibold text-teal-800 dark:text-teal-300">Statistical Superiority:</span>{' '}
            {summaryMessage || 'Top candidate models exhibit statistically significant directional edge over prevailing historical mean under Benjamini-Hochberg FDR (q < 0.05).'}
          </div>
          <Badge variant="outline" className="border-teal-500 text-teal-700 dark:text-teal-300">
            FDR q &lt; 0.05
          </Badge>
        </div>
      )}

      {/* Chart Panel Container */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        {/* Header with Navigation Chips & Table Toggle */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5" role="tablist" aria-label="Model summary charts">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 self-end md:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTableAlt(!showTableAlt)}
              className="text-xs gap-1.5"
              aria-label="Toggle accessible tabular data"
            >
              <TableIcon className="w-3.5 h-3.5" />
              {showTableAlt ? 'Show Visual Chart' : 'Show Data Table'}
            </Button>
          </div>
        </div>

        {/* Chart Family Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800">
          <span className="font-medium text-slate-700 dark:text-slate-300">Model Families:</span>
          {Object.entries(FAMILY_COLORS).map(([fam, color]) => (
            <div key={fam} className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: color }} />
              <span className="capitalize">{fam}</span>
            </div>
          ))}
        </div>

        {/* Chart View or Accessible Table Alternative */}
        {!showTableAlt ? (
          <div>
            {activeTab === 'metric_bars' && <BarErrorPlot chartModels={chartModels} selectedMetric={selectedMetric} />}
            {activeTab === 'phase_heatmap' && <PhaseHeatmapPlot chartModels={chartModels} />}
            {activeTab === 'direction_accuracy' && <DirectionDotPlot chartModels={chartModels} />}
            {activeTab === 'oos_r2' && <OosR2DotPlot chartModels={chartModels} />}
            {activeTab === 'runtime_scatter' && <RuntimeScatterPlot chartModels={chartModels} />}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="p-2">Model</th>
                  <th className="p-2">Family</th>
                  <th className="p-2">Horizon</th>
                  <th className="p-2">Acc (%)</th>
                  <th className="p-2">Acc 95% CI</th>
                  <th className="p-2">OOS R²</th>
                  <th className="p-2">RMSE</th>
                  <th className="p-2">Runtime (s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {chartModels.map((m) => (
                  <tr key={m.model_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50">
                    <td className="p-2 font-medium">{m.model_name}</td>
                    <td className="p-2 capitalize">{m.family}</td>
                    <td className="p-2">h={m.horizon}</td>
                    <td className="p-2 font-mono">{m.accuracy_mean.toFixed(2)}%</td>
                    <td className="p-2 font-mono">[{m.accuracy_ci_lower}%, {m.accuracy_ci_upper}%]</td>
                    <td className="p-2 font-mono">{m.oos_r2_mean.toFixed(4)}</td>
                    <td className="p-2 font-mono">{m.rmse_mean.toFixed(4)}</td>
                    <td className="p-2 font-mono">{m.training_time_s}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
