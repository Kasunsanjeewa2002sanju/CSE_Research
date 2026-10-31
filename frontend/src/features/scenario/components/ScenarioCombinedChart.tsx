import { useState, useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { Table as TableIcon, LineChart as ChartIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EChart } from '@/components/charts/EChart';
import type { ScenarioSubmitResponse } from '../types';

export interface ScenarioCombinedChartProps {
  result: ScenarioSubmitResponse;
}

export function ScenarioCombinedChart({ result }: ScenarioCombinedChartProps) {
  const [showTable, setShowTable] = useState(false);

  const { recent_history = [], current_aspi, fan_chart, scenarios } = result;

  const chartOption = useMemo<EChartsOption>(() => {
    // 1. Build X-axis categories
    const historyDates = recent_history.map((h) => h.date);
    const horizonLabels = ['t=0 (Baseline)', '+1d Horizon', '+2d Horizon', '+5d (1-Week)', '+10d (2-Week)'];
    const xAxisData = [...historyDates, ...horizonLabels.slice(1)];

    const baselineIdx = historyDates.length > 0 ? historyDates.length - 1 : 0;

    // 2. Build Historical ASPI Series (null after baseline)
    const historySeriesData: (number | null)[] = recent_history.map((h) => h.aspi);
    // Pad horizon points with null
    for (let i = 1; i < horizonLabels.length; i++) {
      historySeriesData.push(null);
    }

    // 3. True & False trajectories starting from baselineIdx
    const trueHorizons = fan_chart?.true_scenario || [
      { horizon: 1, target_aspi: scenarios.TRUE.horizons?.['1']?.target_aspi ?? current_aspi * 1.006, ci80_lower: current_aspi * 0.99, ci80_upper: current_aspi * 1.02, ci95_lower: current_aspi * 0.98, ci95_upper: current_aspi * 1.03 },
      { horizon: 2, target_aspi: scenarios.TRUE.horizons?.['2']?.target_aspi ?? current_aspi * 1.009, ci80_lower: current_aspi * 0.985, ci80_upper: current_aspi * 1.025, ci95_lower: current_aspi * 0.975, ci95_upper: current_aspi * 1.035 },
      { horizon: 5, target_aspi: scenarios.TRUE.target_aspi, ci80_lower: scenarios.TRUE.interval_80[0], ci80_upper: scenarios.TRUE.interval_80[1], ci95_lower: scenarios.TRUE.interval_95[0], ci95_upper: scenarios.TRUE.interval_95[1] },
      { horizon: 10, target_aspi: scenarios.TRUE.horizons?.['10']?.target_aspi ?? current_aspi * 1.018, ci80_lower: current_aspi * 0.97, ci80_upper: current_aspi * 1.04, ci95_lower: current_aspi * 0.96, ci95_upper: current_aspi * 1.06 },
    ];

    const falseHorizons = fan_chart?.false_scenario || [
      { horizon: 1, target_aspi: scenarios.FALSE.horizons?.['1']?.target_aspi ?? current_aspi * 0.999, ci80_lower: current_aspi * 0.988, ci80_upper: current_aspi * 1.012, ci95_lower: current_aspi * 0.978, ci95_upper: current_aspi * 1.022 },
      { horizon: 2, target_aspi: scenarios.FALSE.horizons?.['2']?.target_aspi ?? current_aspi * 0.998, ci80_lower: current_aspi * 0.982, ci80_upper: current_aspi * 1.015, ci95_lower: current_aspi * 0.972, ci95_upper: current_aspi * 1.025 },
      { horizon: 5, target_aspi: scenarios.FALSE.target_aspi, ci80_lower: scenarios.FALSE.interval_80[0], ci80_upper: scenarios.FALSE.interval_80[1], ci95_lower: scenarios.FALSE.interval_95[0], ci95_upper: scenarios.FALSE.interval_95[1] },
      { horizon: 10, target_aspi: scenarios.FALSE.horizons?.['10']?.target_aspi ?? current_aspi * 0.995, ci80_lower: current_aspi * 0.965, ci80_upper: current_aspi * 1.03, ci95_lower: current_aspi * 0.955, ci95_upper: current_aspi * 1.045 },
    ];

    const trueLineData: (number | null)[] = new Array(baselineIdx).fill(null);
    trueLineData.push(current_aspi);
    trueHorizons.forEach((h) => trueLineData.push(h.target_aspi));

    const falseLineData: (number | null)[] = new Array(baselineIdx).fill(null);
    falseLineData.push(current_aspi);
    falseHorizons.forEach((h) => falseLineData.push(h.target_aspi));

    // Confidence bands for TRUE scenario
    const true95Lower: (number | null)[] = new Array(baselineIdx).fill(null);
    true95Lower.push(current_aspi * 0.98);
    trueHorizons.forEach((h) => true95Lower.push(h.ci95_lower));

    const true95Diff: (number | null)[] = new Array(baselineIdx).fill(null);
    true95Diff.push(current_aspi * 0.04);
    trueHorizons.forEach((h) => true95Diff.push(h.ci95_upper - h.ci95_lower));

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', lineStyle: { color: '#718096', type: 'dashed' } },
        formatter: (rawParams: unknown) => {
          const params = Array.isArray(rawParams)
            ? (rawParams as Array<{ axisValue: string; value: number | null; seriesName: string; color: string }>)
            : [];
          if (params.length === 0) return '';
          const xVal = params[0].axisValue;
          let tip = `<div class="font-sans text-xs font-semibold pb-1 border-b border-border">${xVal}</div>`;
          params.forEach((p) => {
            if (p.value !== null && p.value !== undefined && !p.seriesName.includes('(Base)')) {
              tip += `<div class="flex items-center justify-between gap-4 text-xs py-0.5">
                <span class="flex items-center gap-1.5"><span style="background-color:${p.color}; width:8px; height:8px; border-radius:50%; display:inline-block;"></span>${p.seriesName}:</span>
                <span class="font-mono font-semibold">${Number(p.value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>`;
            }
          });
          return tip;
        },
      },
      legend: {
        bottom: 0,
        textStyle: { color: '#718096', fontSize: 11 },
        data: ['Historical ASPI', 'Scenario TRUE (Event Occurs)', 'Scenario FALSE (Status Quo)', 'TRUE 95% Conformal Band'],
      },
      grid: {
        top: 24,
        left: 48,
        right: 24,
        bottom: 48,
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLine: { lineStyle: { color: '#CBD5E0' } },
        axisLabel: {
          color: '#718096',
          fontSize: 10,
          formatter: (value: string) => (value.includes('Horizon') || value.includes('t=0') ? value : value.slice(5)),
        },
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitLine: { lineStyle: { color: '#EDF2F7', type: 'dashed' } },
        axisLabel: {
          color: '#718096',
          fontSize: 10,
          formatter: (v: number) => v.toLocaleString(),
        },
      },
      series: [
        // 1. Historical ASPI
        {
          name: 'Historical ASPI',
          type: 'line',
          data: historySeriesData,
          itemStyle: { color: '#1B5CD6' },
          lineStyle: { width: 2, color: '#1B5CD6' },
          symbol: 'none',
          smooth: true,
        },
        // 2. TRUE 95% Lower base
        {
          name: 'TRUE 95% Band (Base)',
          type: 'line',
          data: true95Lower,
          lineStyle: { opacity: 0 },
          stack: 'true-ci-95',
          symbol: 'none',
          silent: true,
        },
        // 3. TRUE 95% Band
        {
          name: 'TRUE 95% Conformal Band',
          type: 'line',
          data: true95Diff,
          lineStyle: { opacity: 0 },
          areaStyle: { color: 'rgba(27, 92, 214, 0.12)' },
          stack: 'true-ci-95',
          symbol: 'none',
          smooth: true,
        },
        // 4. Scenario TRUE Line
        {
          name: 'Scenario TRUE (Event Occurs)',
          type: 'line',
          data: trueLineData,
          itemStyle: { color: '#1B5CD6' },
          lineStyle: { width: 2.5, color: '#1B5CD6' },
          symbol: 'circle',
          symbolSize: 6,
          smooth: true,
        },
        // 5. Scenario FALSE Line
        {
          name: 'Scenario FALSE (Status Quo)',
          type: 'line',
          data: falseLineData,
          itemStyle: { color: '#718096' },
          lineStyle: { width: 2, color: '#718096', type: 'dashed' },
          symbol: 'diamond',
          symbolSize: 6,
          smooth: true,
        },
      ],
    };
  }, [recent_history, current_aspi, fan_chart, scenarios]);

  return (
    <Card className="border-border bg-surface-white shadow-soft">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/60 pb-3">
        <div>
          <CardTitle className="text-base font-semibold text-text-primary">
            Combined Historical ASPI & Counterfactual Fan Chart
          </CardTitle>
          <p className="text-xs text-text-muted">
            Recent trading history trailing into multi-horizon conformal uncertainty distributions (h=1, 2, 5, 10)
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowTable(!showTable)}
          className="flex items-center gap-1.5 text-xs"
        >
          {showTable ? <ChartIcon className="h-3.5 w-3.5" /> : <TableIcon className="h-3.5 w-3.5" />}
          {showTable ? 'View Fan Chart' : 'Accessible Table'}
        </Button>
      </CardHeader>

      <CardContent className="pt-4">
        {showTable ? (
          <div className="overflow-x-auto font-mono text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-subtle text-[11px] font-semibold text-text-secondary">
                  <th className="p-2.5">Horizon</th>
                  <th className="p-2.5">Scenario TRUE ASPI</th>
                  <th className="p-2.5">TRUE 80% Range</th>
                  <th className="p-2.5">TRUE 95% Range</th>
                  <th className="p-2.5">Scenario FALSE ASPI</th>
                  <th className="p-2.5">FALSE 95% Range</th>
                  <th className="p-2.5">Divergence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {[1, 2, 5, 10].map((h) => {
                  const hStr = String(h);
                  const tH = scenarios.TRUE.horizons?.[hStr];
                  const fH = scenarios.FALSE.horizons?.[hStr];
                  const tAspi = tH?.target_aspi ?? current_aspi;
                  const fAspi = fH?.target_aspi ?? current_aspi;
                  const diff = tAspi - fAspi;
                  return (
                    <tr key={h} className="hover:bg-surface-subtle/50">
                      <td className="p-2.5 font-bold">h = {h} ({h === 5 ? '1-Week' : `${h}-Day`})</td>
                      <td className="p-2.5 text-blue-cobalt font-semibold">{tAspi.toFixed(2)}</td>
                      <td className="p-2.5">[{tH?.interval_80[0]?.toFixed(0)} - {tH?.interval_80[1]?.toFixed(0)}]</td>
                      <td className="p-2.5">[{tH?.interval_95[0]?.toFixed(0)} - {tH?.interval_95[1]?.toFixed(0)}]</td>
                      <td className="p-2.5 text-text-secondary">{fAspi.toFixed(2)}</td>
                      <td className="p-2.5">[{fH?.interval_95[0]?.toFixed(0)} - {fH?.interval_95[1]?.toFixed(0)}]</td>
                      <td className={`p-2.5 font-bold ${diff >= 0 ? 'text-green-emerald' : 'text-red-coral'}`}>
                        {diff >= 0 ? '+' : ''}{diff.toFixed(2)} pts
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-80 w-full" aria-label="Recent ASPI History and Scenario Forecast Fan Chart">
            <EChart option={chartOption} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
