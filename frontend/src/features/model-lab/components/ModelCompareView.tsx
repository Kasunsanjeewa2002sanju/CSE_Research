import { useState, useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { EChart } from '@/components/charts/EChart';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { GitCompare, Trophy, Table as TableIcon } from 'lucide-react';
import type { ModelCompareResponse, ModelLeaderboardItem } from '../types';

export interface ModelCompareViewProps {
  compareData: ModelCompareResponse;
  allModels: ModelLeaderboardItem[];
  selectedModelIds: string[];
  onSelectModelIds: (ids: string[]) => void;
}

const PALETTE = ['#0A2A66', '#0095B3', '#3563C1', '#F59E0B'];

export function ModelCompareView({
  compareData,
  allModels,
  selectedModelIds,
  onSelectModelIds,
}: ModelCompareViewProps) {
  const [showTableAlt, setShowTableAlt] = useState(false);

  const toggleModel = (id: string) => {
    if (selectedModelIds.includes(id)) {
      if (selectedModelIds.length > 1) {
        onSelectModelIds(selectedModelIds.filter((x) => x !== id));
      }
    } else {
      if (selectedModelIds.length < 4) {
        onSelectModelIds([...selectedModelIds, id]);
      }
    }
  };

  // 1. Forecast Comparison Chart
  const forecastOption = useMemo<EChartsOption>(() => {
    const dates = compareData.forecast_comparison.map((d) => d.date);
    const seriesList: NonNullable<EChartsOption['series']> = [
      {
        name: 'Actual Return',
        type: 'line',
        data: compareData.forecast_comparison.map((d) => d.actual_return),
        itemStyle: { color: '#0F172A' },
        lineStyle: { width: 3 },
        symbol: 'circle',
        symbolSize: 6,
      },
    ];

    compareData.compared_models.forEach((m, idx) => {
      seriesList.push({
        name: m.model_name,
        type: 'line',
        data: compareData.forecast_comparison.map((d) => d[m.model_id] ?? 0.0),
        itemStyle: { color: PALETTE[idx % PALETTE.length] },
        lineStyle: { width: 2, type: idx === 0 ? 'solid' : 'dashed' },
        symbol: 'circle',
        symbolSize: 4,
      });
    });

    return {
      tooltip: { trigger: 'axis' },
      legend: { top: '2%', textStyle: { fontSize: 11 } },
      grid: { left: '6%', right: '4%', bottom: '12%', top: '16%' },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 25, fontSize: 10 } },
      yAxis: { type: 'value', name: 'Return', splitLine: { lineStyle: { type: 'dashed' } } },
      series: seriesList,
    };
  }, [compareData]);

  // 2. Phase Stability Comparison Chart (R2 across P1..P5)
  const stabilityOption = useMemo<EChartsOption>(() => {
    const phases = ['P1', 'P2', 'P3', 'P4', 'P5'];
    const seriesList = compareData.compared_models.map((m, idx) => ({
      name: m.model_name,
      type: 'bar' as const,
      data: phases.map((p) => m.oos_r2_phases?.[p] ?? 0.0),
      itemStyle: { color: PALETTE[idx % PALETTE.length] },
    }));

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { top: '2%', textStyle: { fontSize: 11 } },
      grid: { left: '8%', right: '4%', bottom: '12%', top: '16%' },
      xAxis: { type: 'category', data: phases, name: 'Phase' },
      yAxis: { type: 'value', name: 'OOS R²', splitLine: { lineStyle: { type: 'dashed' } } },
      series: seriesList,
    };
  }, [compareData]);

  return (
    <div className="space-y-6">
      {/* Model Selection Chips Bar */}
      <div className="bg-card p-4 rounded-lg border border-border shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-primary" />
            <h3 className="font-heading text-sm font-bold text-foreground">
              Select Up to 4 Models to Compare Side by Side
            </h3>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {selectedModelIds.length} / 4 Selected
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {allModels.slice(0, 16).map((m) => {
            const isSelected = selectedModelIds.includes(m.model_id);
            return (
              <button
                key={m.model_id}
                onClick={() => toggleModel(m.model_id)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-mono transition-all border ${
                  isSelected
                    ? 'bg-primary text-primary-foreground border-primary font-semibold shadow-sm'
                    : 'bg-muted/40 text-muted-foreground border-border hover:border-foreground/40'
                }`}
              >
                {m.is_champion && <Trophy className="w-3 h-3 text-amber-400" />}
                <span>{m.model_name}</span>
                <span className="text-[10px] opacity-75">({m.family})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Side-by-Side Metrics Table */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Cross-Model Metrics Comparison Matrix
        </h3>
        <div className="overflow-x-auto rounded border border-border">
          <table className="w-full text-xs font-mono text-left" aria-label="Model comparison table">
            <thead className="bg-muted/60 border-b border-border text-[11px] uppercase text-muted-foreground">
              <tr>
                <th className="p-3">Performance Metric</th>
                {compareData.compared_models.map((m, idx) => (
                  <th key={m.model_id} className="p-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: PALETTE[idx % PALETTE.length] }} />
                      <span className="font-bold text-foreground">{m.model_name}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Family & Horizon</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">
                    <Badge variant="outline" className="uppercase text-[10px]">{m.family}</Badge> (h={m.horizon})
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">OOS R² (Mean ± SD)</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3 font-semibold text-primary">
                    {m.oos_r2_mean.toFixed(4)} ± {m.oos_r2_std.toFixed(4)}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Directional Accuracy</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3 font-semibold text-foreground">
                    {m.accuracy_mean.toFixed(2)}% [{m.accuracy_ci_lower}%, {m.accuracy_ci_upper}%]
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Balanced Accuracy</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">{m.balanced_accuracy_mean.toFixed(2)}%</td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">RMSE Loss</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">{m.rmse_mean.toFixed(4)}</td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Theil's U Statistic</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">{m.theils_u_mean.toFixed(3)}</td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Training Time & Params</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">{m.training_time_s}s ({m.parameters})</td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-muted-foreground">Significance vs Baseline</td>
                {compareData.compared_models.map((m) => (
                  <td key={m.model_id} className="p-3">
                    {m.significantly_better_than_baseline ? (
                      <Badge variant="default" className="bg-teal-600 text-white text-[10px]">
                        Sig. (p={m.p_value_vs_baseline})
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground text-[10px]">Baseline / Not Sig.</span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Forecast Comparison Chart & Phase Stability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Forecast Line Overlay */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-sm font-bold text-foreground">
              Comparative Forecast Trajectory
            </h3>
            <Button size="sm" variant="outline" onClick={() => setShowTableAlt(!showTableAlt)} className="text-xs h-7">
              <TableIcon className="w-3.5 h-3.5 mr-1" /> {showTableAlt ? 'Chart' : 'Table'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Multi-model predicted return trajectories plotted alongside actual ASPI realized returns.
          </p>
          <div className="h-[280px] w-full">
            <EChart option={forecastOption} height="100%" />
          </div>
        </div>

        {/* Phase Stability Comparison */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
          <h3 className="font-heading text-sm font-bold text-foreground">
            Out-of-Sample Phase Stability (P1 to P5)
          </h3>
          <p className="text-xs text-muted-foreground">
            Examining cross-regime consistency across 5 non-overlapping walk-forward eras (1994–2025).
          </p>
          <div className="h-[280px] w-full">
            <EChart option={stabilityOption} height="100%" />
          </div>
        </div>
      </div>
    </div>
  );
}
