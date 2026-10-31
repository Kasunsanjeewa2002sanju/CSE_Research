import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { EChart } from '@/components/charts/EChart';
import type { ModelLeaderboardItem, MetricSortField } from '../types';

export const FAMILY_COLORS: Record<string, string> = {
  shallow: '#0A2A66',
  deep: '#0095B3',
  statistical: '#3563C1',
  foundation: '#4F46E5',
  hybrid: '#0284C7',
  baseline: '#F59E0B',
};

export interface ChartPlotProps {
  chartModels: ModelLeaderboardItem[];
  selectedMetric: MetricSortField;
}

interface CustomRenderApi {
  value: (idx: number) => number;
  coord: (pt: [number, number]) => [number, number];
  style: () => Record<string, unknown>;
}

export function BarErrorPlot({ chartModels, selectedMetric }: ChartPlotProps) {
  const option = useMemo<EChartsOption>(() => {
    const categories = chartModels.map((m) => m.model_name.replace(' (Set ', '\n(Set '));
    const isAcc = selectedMetric === 'directional_accuracy' || selectedMetric === 'balanced_accuracy';

    const values = chartModels.map((m) => {
      if (selectedMetric === 'oos_r2') return m.oos_r2_mean;
      if (selectedMetric === 'directional_accuracy') return m.accuracy_mean;
      if (selectedMetric === 'balanced_accuracy') return m.balanced_accuracy_mean;
      if (selectedMetric === 'rmse') return m.rmse_mean;
      if (selectedMetric === 'mae') return m.mae_mean;
      return m.theils_u_mean;
    });

    const errorBars = chartModels.map((m, idx) => {
      const val = values[idx];
      const std =
        selectedMetric === 'oos_r2'
          ? m.oos_r2_std
          : selectedMetric === 'directional_accuracy'
            ? m.accuracy_std
            : selectedMetric === 'balanced_accuracy'
              ? m.balanced_accuracy_std
              : m.rmse_std;
      return [idx, val - std, val + std];
    });

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const items = params as { dataIndex: number; value: number }[];
          const item = items[0];
          const m = chartModels[item.dataIndex];
          return `<strong>${m.model_name}</strong><br/>` +
            `Family: ${m.family} | Horizon: h=${m.horizon}<br/>` +
            `Mean: ${item.value.toFixed(4)}<br/>` +
            `Std across phases: ±${(selectedMetric === 'oos_r2' ? m.oos_r2_std : m.accuracy_std).toFixed(4)}`;
        },
      },
      grid: { left: '8%', right: '5%', bottom: '22%', top: '10%' },
      xAxis: { type: 'category', data: categories, axisLabel: { interval: 0, rotate: 20, fontSize: 10 } },
      yAxis: {
        type: 'value',
        name: selectedMetric.toUpperCase(),
        axisLabel: { formatter: isAcc ? '{value}%' : '{value}' },
      },
      series: [
        {
          name: 'Mean across phases',
          type: 'bar',
          data: chartModels.map((m, idx) => ({
            value: values[idx],
            itemStyle: { color: FAMILY_COLORS[m.family] || '#3563C1' },
          })),
        },
        {
          type: 'custom',
          name: 'Error Bar (±1 SD)',
          itemStyle: { borderWidth: 1.5, color: '#1E293B' },
          renderItem: (_params: unknown, api: unknown) => {
            const a = api as CustomRenderApi;
            const xVal = a.value(0);
            const low = a.coord([xVal, a.value(1)]);
            const high = a.coord([xVal, a.value(2)]);
            const halfWidth = 6;
            return {
              type: 'group',
              children: [
                { type: 'line', shape: { x1: low[0], y1: low[1], x2: high[0], y2: high[1] }, style: a.style() },
                { type: 'line', shape: { x1: low[0] - halfWidth, y1: low[1], x2: low[0] + halfWidth, y2: low[1] }, style: a.style() },
                { type: 'line', shape: { x1: high[0] - halfWidth, y1: high[1], x2: high[0] + halfWidth, y2: high[1] }, style: a.style() },
              ],
            };
          },
          data: errorBars,
        },
      ],
    };
  }, [chartModels, selectedMetric]);

  return <EChart option={option} className="h-80 w-full" aria-label="Metric Bar Chart with Error Bars" />;
}

export function PhaseHeatmapPlot({ chartModels }: { chartModels: ModelLeaderboardItem[] }) {
  const option = useMemo<EChartsOption>(() => {
    const phases = ['P1', 'P2', 'P3', 'P4', 'P5'];
    const modelNames = chartModels.map((m) => m.model_name);
    const data: [number, number, number][] = [];

    chartModels.forEach((m, mIdx) => {
      phases.forEach((p, pIdx) => {
        const val = m.oos_r2_phases?.[p] ?? 0.0;
        data.push([pIdx, mIdx, val]);
      });
    });

    return {
      tooltip: {
        position: 'top',
        formatter: (params: unknown) => {
          const p = params as { data: [number, number, number] };
          const val = p.data[2];
          return `Phase ${phases[p.data[0]]} — ${modelNames[p.data[1]]}<br/>OOS R²: <strong>${val.toFixed(4)}</strong>`;
        },
      },
      grid: { left: '20%', right: '8%', bottom: '12%', top: '10%' },
      xAxis: { type: 'category', data: phases, splitArea: { show: true } },
      yAxis: { type: 'category', data: modelNames, splitArea: { show: true }, axisLabel: { fontSize: 10 } },
      visualMap: {
        min: -0.05,
        max: 0.12,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: { color: ['#EDF2FB', '#3563C1', '#0A2A66', '#0095B3'] },
      },
      series: [
        {
          name: 'OOS R²',
          type: 'heatmap',
          data,
          label: {
            show: true,
            formatter: (params: unknown) => {
              const p = params as { data: [number, number, number] };
              return p.data[2].toFixed(3);
            },
            fontSize: 9,
          },
        },
      ],
    };
  }, [chartModels]);

  return <EChart option={option} className="h-80 w-full" aria-label="Phase by Model Heatmap" />;
}

export function DirectionDotPlot({ chartModels }: { chartModels: ModelLeaderboardItem[] }) {
  const option = useMemo<EChartsOption>(() => {
    const categories = chartModels.map((m) => m.model_name);
    const dots = chartModels.map((m, idx) => ({
      value: [m.accuracy_mean, idx],
      itemStyle: { color: FAMILY_COLORS[m.family] || '#3563C1' },
    }));

    const whiskers = chartModels.map((m, idx) => [idx, m.accuracy_ci_lower, m.accuracy_ci_upper]);

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: unknown) => {
          const param = params as { dataIndex: number };
          const m = chartModels[param.dataIndex];
          return `<strong>${m.model_name}</strong><br/>Directional Accuracy: <strong>${m.accuracy_mean}%</strong><br/>95% CI: [${m.accuracy_ci_lower}%, ${m.accuracy_ci_upper}%]`;
        },
      },
      grid: { left: '22%', right: '8%', bottom: '10%', top: '8%' },
      xAxis: {
        type: 'value',
        min: 45,
        max: 68,
        axisLabel: { formatter: '{value}%' },
        splitLine: { lineStyle: { type: 'dashed' } },
      },
      yAxis: { type: 'category', data: categories, axisLabel: { fontSize: 10 } },
      series: [
        {
          name: 'Direction Accuracy',
          type: 'scatter',
          symbolSize: 12,
          data: dots,
          markLine: {
            symbol: 'none',
            data: [{ xAxis: 50.0, lineStyle: { color: '#F59E0B', type: 'dashed', width: 2 }, label: { formatter: '50% Null' } }],
          },
        },
        {
          type: 'custom',
          name: '95% CI',
          itemStyle: { borderWidth: 1.5, color: '#475569' },
          renderItem: (_params: unknown, api: unknown) => {
            const a = api as CustomRenderApi;
            const yVal = a.value(0);
            const low = a.coord([a.value(1), yVal]);
            const high = a.coord([a.value(2), yVal]);
            const halfH = 4;
            return {
              type: 'group',
              children: [
                { type: 'line', shape: { x1: low[0], y1: low[1], x2: high[0], y2: high[1] }, style: a.style() },
                { type: 'line', shape: { x1: low[0], y1: low[1] - halfH, x2: low[0], y2: low[1] + halfH }, style: a.style() },
                { type: 'line', shape: { x1: high[0], y1: high[1] - halfH, x2: high[0], y2: high[1] + halfH }, style: a.style() },
              ],
            };
          },
          data: whiskers,
        },
      ],
    };
  }, [chartModels]);

  return <EChart option={option} className="h-80 w-full" aria-label="Directional Accuracy Dot Plot with 50% Reference" />;
}

export function OosR2DotPlot({ chartModels }: { chartModels: ModelLeaderboardItem[] }) {
  const option = useMemo<EChartsOption>(() => {
    const categories = chartModels.map((m) => m.model_name);
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: unknown) => {
          const p = params as { dataIndex: number };
          const m = chartModels[p.dataIndex];
          return `<strong>${m.model_name}</strong><br/>OOS R²: <strong>${m.oos_r2_mean.toFixed(4)}</strong> ± ${m.oos_r2_std.toFixed(4)}`;
        },
      },
      grid: { left: '22%', right: '8%', bottom: '10%', top: '8%' },
      xAxis: { type: 'value', min: -0.04, max: 0.12, splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: categories, axisLabel: { fontSize: 10 } },
      series: [
        {
          name: 'OOS R²',
          type: 'scatter',
          symbolSize: 12,
          data: chartModels.map((m, idx) => ({
            value: [m.oos_r2_mean, idx],
            itemStyle: { color: FAMILY_COLORS[m.family] || '#3563C1' },
          })),
          markLine: {
            symbol: 'none',
            data: [{ xAxis: 0.0, lineStyle: { color: '#F59E0B', type: 'dashed', width: 2 }, label: { formatter: 'R²=0 Baseline' } }],
          },
        },
      ],
    };
  }, [chartModels]);

  return <EChart option={option} className="h-80 w-full" aria-label="Out of Sample R-Squared Dot Plot with Zero Line" />;
}

export function RuntimeScatterPlot({ chartModels }: { chartModels: ModelLeaderboardItem[] }) {
  const option = useMemo<EChartsOption>(() => {
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: unknown) => {
          const p = params as { data: { name: string; family: string; value: [number, number] } };
          const d = p.data;
          return `<strong>${d.name}</strong><br/>Family: ${d.family}<br/>Runtime: ${d.value[0]}s<br/>Accuracy: ${d.value[1]}%`;
        },
      },
      grid: { left: '10%', right: '8%', bottom: '12%', top: '10%' },
      xAxis: { type: 'log', name: 'Training Runtime (seconds, log scale)', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'value', name: 'Directional Accuracy (%)', min: 48, max: 65, splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          type: 'scatter',
          symbolSize: 14,
          data: chartModels.map((m) => ({
            name: m.model_name,
            family: m.family,
            value: [Math.max(0.01, m.training_time_s), m.accuracy_mean],
            itemStyle: { color: FAMILY_COLORS[m.family] || '#3563C1' },
          })),
        },
      ],
    };
  }, [chartModels]);

  return <EChart option={option} className="h-80 w-full" aria-label="Accuracy versus Training Runtime Scatter Plot" />;
}
