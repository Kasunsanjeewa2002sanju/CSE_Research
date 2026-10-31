import { useMemo, useState } from 'react';
import type { EChartsOption } from 'echarts';
import { EChart } from '@/components/charts/EChart';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Cpu, HardDrive, Hash, Calendar, Clock, Table as TableIcon } from 'lucide-react';
import type { ModelDetailResponse } from '../types';

export interface ModelDetailForecastProps {
  detail: ModelDetailResponse;
}

export function ModelDetailForecast({ detail }: ModelDetailForecastProps) {
  const [showTableAlt, setShowTableAlt] = useState(false);

  // 1. Forecast vs Actual Chart with Confidence Interval & Shaded Validation Block
  const forecastOption = useMemo<EChartsOption>(() => {
    const dates = detail.per_phase_predictions.map((p) => p.date);
    const actuals = detail.per_phase_predictions.map((p) => p.actual_return);
    const preds = detail.per_phase_predictions.map((p) => p.predicted_return);
    const ciLow = detail.per_phase_predictions.map((p) => p.ci_lower ?? p.predicted_return - 0.015);
    const ciDiff = detail.per_phase_predictions.map((p) => (p.ci_upper ?? p.predicted_return + 0.015) - (p.ci_lower ?? p.predicted_return - 0.015));

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const items = params as { axisValue: string; marker: string; seriesName: string; value: number }[];
          let str = `<strong>Date: ${items[0].axisValue}</strong><br/>`;
          items.forEach((item) => {
            if (item.seriesName === 'CI Base') return;
            str += `${item.marker} ${item.seriesName}: <strong>${Number(item.value).toFixed(4)}</strong><br/>`;
          });
          return str;
        },
      },
      legend: { data: ['Actual ASPI Return', 'Predicted Return', '95% Forecast Interval'], top: '2%' },
      grid: { left: '6%', right: '4%', bottom: '12%', top: '14%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { rotate: 25, fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        name: 'Return',
        axisLabel: { formatter: (val: number) => val.toFixed(3) },
        splitLine: { lineStyle: { type: 'dashed' } },
      },
      series: [
        {
          name: 'CI Base',
          type: 'line',
          data: ciLow,
          lineStyle: { opacity: 0 },
          stack: 'confidence-band',
          symbol: 'none',
        },
        {
          name: '95% Forecast Interval',
          type: 'line',
          data: ciDiff,
          lineStyle: { opacity: 0 },
          areaStyle: { color: 'rgba(0, 149, 179, 0.15)' },
          stack: 'confidence-band',
          symbol: 'none',
        },
        {
          name: 'Actual ASPI Return',
          type: 'line',
          data: actuals,
          itemStyle: { color: '#0A2A66' },
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          markArea: {
            itemStyle: { color: 'rgba(0, 149, 179, 0.06)' },
            data: [[{ name: 'Validation Block (P5)', xAxis: dates[0] }, { xAxis: dates[dates.length - 1] }]],
          },
        },
        {
          name: 'Predicted Return',
          type: 'line',
          data: preds,
          itemStyle: { color: '#0095B3' },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'circle',
          symbolSize: 4,
        },
      ],
    };
  }, [detail]);

  // 2. Cumulative Error Chart (Cumulative MAE & RMSE)
  const cumulativeErrorOption = useMemo<EChartsOption>(() => {
    const dates = detail.cumulative_error.map((e) => e.date);
    const maes = detail.cumulative_error.map((e) => e.cumulative_mae);
    const rmses = detail.cumulative_error.map((e) => e.cumulative_rmse);

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['Cumulative MAE', 'Cumulative RMSE'], top: '2%' },
      grid: { left: '6%', right: '4%', bottom: '12%', top: '14%' },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 25, fontSize: 10 } },
      yAxis: { type: 'value', name: 'Loss', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: 'Cumulative MAE',
          type: 'line',
          data: maes,
          itemStyle: { color: '#3563C1' },
          lineStyle: { width: 2 },
          symbol: 'none',
        },
        {
          name: 'Cumulative RMSE',
          type: 'line',
          data: rmses,
          itemStyle: { color: '#0A2A66' },
          lineStyle: { width: 2 },
          symbol: 'none',
        },
      ],
    };
  }, [detail]);

  return (
    <div className="space-y-6">
      {/* Top Metadata Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-sans">
            <Calendar className="w-3.5 h-3.5 text-primary" /> Training Range
          </div>
          <div className="font-mono text-xs font-semibold text-foreground mt-1">
            {detail.training_data_range[0]} to {detail.training_data_range[1]}
          </div>
        </div>

        <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-sans">
            <Hash className="w-3.5 h-3.5 text-primary" /> Seed
          </div>
          <div className="font-mono text-xs font-semibold text-foreground mt-1">
            Seed = {detail.seed}
          </div>
        </div>

        <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-sans">
            <Clock className="w-3.5 h-3.5 text-primary" /> Runtime
          </div>
          <div className="font-mono text-xs font-semibold text-foreground mt-1">
            {detail.runtime_seconds}s
          </div>
        </div>

        <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-sans">
            <HardDrive className="w-3.5 h-3.5 text-primary" /> Memory
          </div>
          <div className="font-mono text-xs font-semibold text-foreground mt-1">
            {detail.memory_mb} MB
          </div>
        </div>

        <div className="bg-card p-3 rounded-lg border border-border shadow-sm col-span-2">
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-sans">
            <Cpu className="w-3.5 h-3.5 text-primary" /> Hardware Architecture
          </div>
          <div className="font-mono text-xs font-semibold text-foreground mt-1 truncate" title={detail.hardware}>
            {detail.hardware}
          </div>
        </div>
      </div>

      {/* Hyperparameters Pill Bar */}
      <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
        <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-2 font-heading">
          Model Hyperparameters (Frozen Calibration)
        </h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(detail.hyperparameters).map(([k, v]) => (
            <Badge key={k} variant="secondary" className="font-mono text-[11px] px-2 py-0.5">
              <span className="text-muted-foreground mr-1">{k}:</span>
              <span className="font-semibold text-foreground">{String(v)}</span>
            </Badge>
          ))}
        </div>
      </div>

      {/* Forecast vs Actual Chart Card */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading text-sm font-bold text-foreground">
              Per-Phase Out-of-Sample Forecast versus Actual ASPI Return
            </h3>
            <p className="text-xs text-muted-foreground">
              Out-of-sample test trajectory with shaded validation block and 95% forecast intervals.
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowTableAlt(!showTableAlt)}
            className="text-xs h-7"
          >
            <TableIcon className="w-3.5 h-3.5 mr-1" /> {showTableAlt ? 'View Chart' : 'Table View'}
          </Button>
        </div>

        {showTableAlt ? (
          <div className="overflow-x-auto max-h-[340px]">
            <table className="w-full text-xs font-mono border-collapse" aria-label="Forecast vs actual table">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left">
                  <th className="p-2">Date</th>
                  <th className="p-2">Actual Return</th>
                  <th className="p-2">Predicted</th>
                  <th className="p-2">Residual</th>
                  <th className="p-2">95% CI</th>
                </tr>
              </thead>
              <tbody>
                {detail.per_phase_predictions.map((p) => (
                  <tr key={p.date} className="border-b border-border/50">
                    <td className="p-2">{p.date}</td>
                    <td className="p-2 font-semibold">{p.actual_return.toFixed(4)}</td>
                    <td className="p-2 text-primary">{p.predicted_return.toFixed(4)}</td>
                    <td className="p-2">{p.residual.toFixed(4)}</td>
                    <td className="p-2">[{p.ci_lower?.toFixed(4)}, {p.ci_upper?.toFixed(4)}]</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-[340px] w-full">
            <EChart option={forecastOption} height="100%" />
          </div>
        )}
      </div>

      {/* Cumulative Error Card */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Cumulative Evaluation Loss (MAE & RMSE Tracking)
        </h3>
        <p className="text-xs text-muted-foreground">
          Tracking rolling cumulative out-of-sample error across trading sessions.
        </p>
        <div className="h-[240px] w-full">
          <EChart option={cumulativeErrorOption} height="100%" />
        </div>
      </div>
    </div>
  );
}
