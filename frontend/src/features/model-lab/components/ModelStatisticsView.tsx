import { useMemo, useState } from 'react';
import type { EChartsOption } from 'echarts';
import { EChart } from '@/components/charts/EChart';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { CheckCircle2, XCircle, Award, Layers, Table as TableIcon } from 'lucide-react';
import type { ModelStatisticsResponse } from '../types';

export interface ModelStatisticsViewProps {
  stats: ModelStatisticsResponse;
}

export function ModelStatisticsView({ stats }: ModelStatisticsViewProps) {
  const [showTableAlt, setShowTableAlt] = useState(false);

  // 1. Diebold-Mariano Pairwise P-Value Heatmap
  const dmHeatmapOption = useMemo<EChartsOption>(() => {
    const models = stats.matrix_models;
    const data: [number, number, number][] = [];

    stats.dm_matrix.forEach((cell) => {
      const idxA = models.indexOf(cell.model_a);
      const idxB = models.indexOf(cell.model_b);
      if (idxA !== -1 && idxB !== -1) {
        data.push([idxA, idxB, cell.p_value]);
      }
    });

    return {
      tooltip: {
        position: 'top',
        formatter: (params: unknown) => {
          const p = params as { data: [number, number, number] };
          const ma = models[p.data[0]];
          const mb = models[p.data[1]];
          const val = p.data[2];
          return `<strong>${ma}</strong> vs <strong>${mb}</strong><br/>DM p-value: <strong>${val.toFixed(4)}</strong> ${val < 0.05 ? '(p < 0.05 Significant)' : ''}`;
        },
      },
      grid: { left: '22%', right: '8%', bottom: '15%', top: '10%' },
      xAxis: { type: 'category', data: models, axisLabel: { rotate: 20, fontSize: 9 } },
      yAxis: { type: 'category', data: models, axisLabel: { fontSize: 9 } },
      visualMap: {
        min: 0.0,
        max: 1.0,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: { color: ['#0A2A66', '#3563C1', '#EDF2FB'] },
      },
      series: [
        {
          name: 'DM p-value',
          type: 'heatmap',
          data,
          label: {
            show: true,
            formatter: (params: unknown) => {
              const param = params as { data: [number, number, number] };
              const v = param.data[2];
              return v < 0.01 ? `${v.toFixed(3)}**` : v < 0.05 ? `${v.toFixed(3)}*` : v.toFixed(3);
            },
            fontSize: 9,
          },
        },
      ],
    };
  }, [stats]);

  // 2. Feature Sets Ablation Chart (Set A vs B vs C)
  const ablationChartOption = useMemo<EChartsOption>(() => {
    const topAblations = stats.ablation_feature_sets.slice(0, 5);
    const architectures = topAblations.map((a) => a.architecture);

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['Set A (Technical)', 'Set B (+ Macro)', 'Set C (+ News/Events)'], top: '2%' },
      grid: { left: '20%', right: '6%', bottom: '10%', top: '16%' },
      xAxis: { type: 'value', name: 'OOS R²', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: architectures, axisLabel: { fontSize: 10 } },
      series: [
        { name: 'Set A (Technical)', type: 'bar', data: topAblations.map((a) => a.r2_set_a), itemStyle: { color: '#3563C1' } },
        { name: 'Set B (+ Macro)', type: 'bar', data: topAblations.map((a) => a.r2_set_b), itemStyle: { color: '#0095B3' } },
        { name: 'Set C (+ News/Events)', type: 'bar', data: topAblations.map((a) => a.r2_set_c), itemStyle: { color: '#0A2A66' } },
      ],
    };
  }, [stats]);

  return (
    <div className="space-y-6">
      {/* Top Row: Diebold-Mariano Heatmap & Model Confidence Set */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* DM Matrix Card */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-sm font-bold text-foreground">
              Pairwise Diebold-Mariano Loss Differential Matrix
            </h3>
            <Badge variant="outline" className="font-mono text-[10px]">
              Harvey-Leybourne-Newbold (HLN)
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground font-sans">
            Two-sided asymptotic p-values with asterisks denoting statistical significance at 5% (*) and 1% (**).
          </p>
          <div className="h-[280px] w-full">
            <EChart option={dmHeatmapOption} height="100%" />
          </div>
        </div>

        {/* Model Confidence Set (MCS) Card */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-sm font-bold text-foreground flex items-center gap-1.5">
              <Award className="w-4 h-4 text-primary" /> Model Confidence Set (MCS) Membership
            </h3>
            <Badge variant="default" className="bg-primary text-primary-foreground font-mono text-[10px]">
              {(stats.model_confidence_set.confidence_level * 100).toFixed(0)}% Confidence
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground font-sans">
            Hansen, Lunde & Nason (2011) iterative test of superior predictive ability across loss differentials.
          </p>

          <div className="space-y-2 mt-2">
            <div className="text-xs font-semibold text-foreground uppercase tracking-wider font-heading">
              Included in 95% Confidence Set:
            </div>
            <div className="space-y-1.5">
              {stats.model_confidence_set.included_models.map((item: Record<string, unknown>, idx: number) => {
                const modelName = String(item.model || item.model_id || 'Model');
                const pVal = typeof item.p_value === 'number' ? item.p_value.toFixed(4) : String(item.p_value ?? '');
                return (
                  <div key={idx} className="flex items-center justify-between bg-primary/5 border border-primary/20 p-2 rounded text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                      <span className="font-semibold text-foreground">{modelName}</span>
                    </div>
                    <span className="text-muted-foreground">MCS p-val: {pVal}</span>
                  </div>
                );
              })}
            </div>

            <div className="text-xs font-semibold text-foreground uppercase tracking-wider font-heading pt-2">
              Eliminated Models:
            </div>
            <div className="space-y-1.5">
              {stats.model_confidence_set.excluded_models.map((item: Record<string, unknown>, idx: number) => {
                const modelName = String(item.model || item.model_id || 'Model');
                const stage = String(item.elimination_stage || item.elimination_step || idx + 1);
                const pVal = typeof item.p_value === 'number' ? item.p_value.toFixed(4) : String(item.p_value ?? '');
                return (
                  <div key={idx} className="flex items-center justify-between bg-muted/40 border border-border p-2 rounded text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <XCircle className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-muted-foreground">{modelName}</span>
                    </div>
                    <span className="text-[10px] text-muted-foreground">Eliminated Stage {stage} (p={pVal})</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Feature Sets Ablation Study */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            <h3 className="font-heading text-sm font-bold text-foreground">
              Feature Set Ablation Study (Set A vs Set B vs Set C)
            </h3>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowTableAlt(!showTableAlt)} className="text-xs h-7">
            <TableIcon className="w-3.5 h-3.5 mr-1" /> {showTableAlt ? 'View Chart' : 'Ablation Table'}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground font-sans">
          Evaluating marginal predictive utility when progressing from Price (A) to Macroeconomic (B) to News/Election cycle indicators (C).
        </p>

        {showTableAlt ? (
          <div className="overflow-x-auto rounded border border-border max-h-[300px]">
            <table className="w-full text-xs font-mono text-left" aria-label="Feature ablation table">
              <thead className="bg-muted/50 border-b border-border text-[10px] uppercase text-muted-foreground">
                <tr>
                  <th className="p-2.5">Architecture</th>
                  <th className="p-2.5">Set A R²</th>
                  <th className="p-2.5">Set B R²</th>
                  <th className="p-2.5">Set C R²</th>
                  <th className="p-2.5">Δ R² (C - A)</th>
                  <th className="p-2.5">t-stat (C vs A)</th>
                  <th className="p-2.5">p-val (C vs A)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {stats.ablation_feature_sets.map((row) => (
                  <tr key={row.architecture + row.horizon} className="hover:bg-muted/30">
                    <td className="p-2.5 font-semibold text-foreground">{row.architecture} (h={row.horizon})</td>
                    <td className="p-2.5">{row.r2_set_a.toFixed(4)}</td>
                    <td className="p-2.5">{row.r2_set_b.toFixed(4)}</td>
                    <td className="p-2.5 font-semibold text-primary">{row.r2_set_c.toFixed(4)}</td>
                    <td className="p-2.5">{row.delta_r2_c_minus_a > 0 ? `+${row.delta_r2_c_minus_a.toFixed(4)}` : row.delta_r2_c_minus_a.toFixed(4)}</td>
                    <td className="p-2.5">{row.t_stat_c_vs_a}</td>
                    <td className="p-2.5">{row.p_val_c_vs_a < 0.05 ? `${row.p_val_c_vs_a} (Sig.)` : row.p_val_c_vs_a}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-[260px] w-full">
            <EChart option={ablationChartOption} height="100%" />
          </div>
        )}
      </div>

      {/* Event Window vs Non-Event Window Table */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Event-Window versus Non-Event-Window Performance
        </h3>
        <p className="text-xs text-muted-foreground font-sans">
          Evaluating predictability breakdown between active electoral event windows vs baseline CSE trading days (with sample size n).
        </p>

        <div className="overflow-x-auto rounded border border-border">
          <table className="w-full text-xs font-mono text-left" aria-label="Event window ablation table">
            <thead className="bg-muted/50 border-b border-border text-[10px] uppercase text-muted-foreground">
              <tr>
                <th className="p-2.5">Model</th>
                <th className="p-2.5">Phase</th>
                <th className="p-2.5">n (Inside)</th>
                <th className="p-2.5">n (Outside)</th>
                <th className="p-2.5">R² (Inside Events)</th>
                <th className="p-2.5">R² (Outside Events)</th>
                <th className="p-2.5">Δ R² (In - Out)</th>
                <th className="p-2.5">DA (Inside)</th>
                <th className="p-2.5">DA (Outside)</th>
                <th className="p-2.5">PT Test p-val</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {stats.ablation_event_windows.map((row, idx) => (
                <tr key={idx} className="hover:bg-muted/30">
                  <td className="p-2.5 font-semibold text-foreground">{row.model}</td>
                  <td className="p-2.5"><Badge variant="outline" className="text-[10px]">{row.phase}</Badge></td>
                  <td className="p-2.5">{row.n_inside_events}</td>
                  <td className="p-2.5 text-muted-foreground">{row.n_outside_events}</td>
                  <td className="p-2.5 font-semibold text-primary">{row.r2_inside.toFixed(4)}</td>
                  <td className="p-2.5 text-muted-foreground">{row.r2_outside.toFixed(4)}</td>
                  <td className="p-2.5">{row.delta_r2_in_minus_out > 0 ? `+${row.delta_r2_in_minus_out.toFixed(4)}` : row.delta_r2_in_minus_out.toFixed(4)}</td>
                  <td className="p-2.5 font-semibold text-foreground">{row.acc_inside.toFixed(2)}%</td>
                  <td className="p-2.5 text-muted-foreground">{row.acc_outside.toFixed(2)}%</td>
                  <td className="p-2.5">{row.pt_pval_inside < 0.05 ? `${row.pt_pval_inside} (Sig.)` : row.pt_pval_inside}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
