import type { EChartsOption } from 'echarts';
import type {
  CaarDataPoint,
  IndividualEventStudyPath,
  EventStudyHeatmapResponse,
  EventStudyPerEventItem,
  PermutationDistribution,
  TrajectoryDisplayMode,
} from '../types';

export function buildCaarTrajectoryOption(
  data: CaarDataPoint[],
  individualEvents: IndividualEventStudyPath[] = [],
  displayMode: TrajectoryDisplayMode = 'both'
): EChartsOption {
  const days = data.map((d) => d.day);
  const meanCaar = data.map((d) => d.caar);
  const ciLower = data.map((d) => d.ci_lower_95);
  const ciDiff = data.map((d) => d.ci_upper_95 - d.ci_lower_95);

  const series: EChartsOption['series'] = [];

  // 1. Shaded Permutation 95% Confidence Band (Custom Polygon)
  // Handles positive, negative, and zero-crossing bounds without any ECharts stack bugs
  series.push({
    name: '95% Permutation Band',
    type: 'custom',
    renderItem: (params, api) => {
      if (params.dataIndex !== 0) return;
      const upperPoints: [number, number][] = [];
      const lowerPoints: [number, number][] = [];
      for (let i = 0; i < data.length; i++) {
        upperPoints.push(api.coord([i, data[i].ci_upper_95]) as [number, number]);
        lowerPoints.push(api.coord([i, data[i].ci_lower_95]) as [number, number]);
      }
      const points = upperPoints.concat(lowerPoints.reverse());
      return {
        type: 'polygon',
        shape: { points },
        style: {
          fill: 'rgba(18, 70, 179, 0.14)',
          stroke: 'transparent',
        },
      };
    },
    data: data.map((_, i) => [i, data[i].ci_lower_95, data[i].ci_upper_95]),
    silent: true,
    z: 1,
  });

  // 1b. Subtle boundary lines for 95% Confidence Band
  series.push({
    name: '95% CI Lower',
    type: 'line',
    data: data.map((d) => d.ci_lower_95),
    lineStyle: { color: 'rgba(18, 70, 179, 0.35)', width: 1, type: 'dashed' },
    symbol: 'none',
    silent: true,
    z: 1,
  });
  series.push({
    name: '95% CI Upper',
    type: 'line',
    data: data.map((d) => d.ci_upper_95),
    lineStyle: { color: 'rgba(18, 70, 179, 0.35)', width: 1, type: 'dashed' },
    symbol: 'none',
    silent: true,
    z: 1,
  });

  // 2. Individual Events (Light lines with hover emphasis)
  if (displayMode === 'both' || displayMode === 'actual') {
    individualEvents.forEach((ev) => {
      const pointMap = new Map(ev.path.map((p) => [p.day, p.car]));
      const evData = days.map((d) => pointMap.get(d) ?? null);

      series.push({
        name: ev.name,
        type: 'line',
        data: evData,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#53627A',
          width: 1,
          opacity: 0.25,
        },
        emphasis: {
          focus: 'series',
          lineStyle: {
            color: '#0095B3',
            width: 2.5,
            opacity: 0.95,
          },
        },
      });
    });
  }

  // 3. Highlighted Mean CAAR Path
  series.push({
    name: 'Mean CAAR Path',
    type: 'line',
    data: meanCaar,
    smooth: true,
    symbol: 'circle',
    symbolSize: (_val: unknown, params: { dataIndex: number }) =>
      days[params.dataIndex] === 0 ? 8 : 4,
    lineStyle: {
      color: '#0A2A66',
      width: 3.5,
    },
    itemStyle: {
      color: '#0A2A66',
    },
    z: 3,
    markLine: {
      symbol: ['none', 'none'],
      data: [
        {
          xAxis: 't=0',
          lineStyle: { color: '#0095B3', type: 'dashed', width: 2 },
          label: {
            formatter: 'Event Day (t=0)',
            position: 'insideEndTop',
            color: '#0095B3',
            fontSize: 11,
          },
        },
        {
          yAxis: 0,
          lineStyle: { color: 'rgba(83, 98, 122, 0.4)', type: 'solid', width: 1 },
        },
      ],
    },
  });

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 42, 102, 0.95)',
      borderColor: '#1246B3',
      textStyle: { color: '#FFFFFF', fontSize: 12 },
      formatter: (params: unknown) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const day = days[params[0].dataIndex];
        const dayLabel =
          day === 0 ? 'Reaction Date (t = 0)' : `t = ${day > 0 ? `+${day}` : day} TD`;
        let out = `<div class="font-bold pb-1 mb-1 border-b border-white/20">${dayLabel}</div>`;
        const meanPoint = data[params[0].dataIndex];
        if (meanPoint) {
          out += `<div class="flex justify-between gap-4 py-0.5"><span>Mean CAAR:</span><span class="font-mono font-bold">${meanPoint.caar > 0 ? `+${meanPoint.caar}` : meanPoint.caar}%</span></div>`;
          out += `<div class="flex justify-between gap-4 text-xs text-white/70"><span>95% CI:</span><span class="font-mono">[${meanPoint.ci_lower_95}%, ${meanPoint.ci_upper_95}%]</span></div>`;
        }
        return out;
      },
    },
    grid: { left: 55, right: 25, top: 25, bottom: 35, containLabel: true },
    xAxis: {
      type: 'category',
      data: days.map((d) => (d === 0 ? 't=0' : d > 0 ? `+${d}` : `${d}`)),
      axisLabel: { color: '#53627A', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.3)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#53627A',
        formatter: (val: number) => `${val > 0 ? `+${val}` : val}%`,
        fontSize: 11,
      },
      splitLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.15)' } },
    },
    series,
  };
}

export function buildAbnormalReturnBarsOption(data: CaarDataPoint[]): EChartsOption {
  const days = data.map((d) => d.day);
  const arValues = data.map((d) => d.ar ?? 0);

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 42, 102, 0.95)',
      borderColor: '#1246B3',
      textStyle: { color: '#FFFFFF', fontSize: 12 },
      formatter: (params: unknown) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const idx = params[0].dataIndex;
        const pt = data[idx];
        const dayLabel =
          pt.day === 0 ? 'Reaction Day (t = 0)' : `Day t = ${pt.day > 0 ? `+${pt.day}` : pt.day}`;
        return `
          <div class="font-bold pb-1 mb-1 border-b border-white/20">${dayLabel}</div>
          <div class="flex justify-between gap-4"><span>Daily Abnormal Return:</span><span class="font-mono font-bold">${pt.ar && pt.ar > 0 ? `+${pt.ar}` : pt.ar}%</span></div>
          ${pt.ar_t_stat ? `<div class="flex justify-between gap-4 text-xs text-white/70"><span>t-stat:</span><span class="font-mono">${pt.ar_t_stat} (p = ${pt.ar_p_val})</span></div>` : ''}
        `;
      },
    },
    grid: { left: 55, right: 25, top: 20, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: days.map((d) => (d === 0 ? 't=0' : d > 0 ? `+${d}` : `${d}`)),
      axisLabel: { color: '#53627A', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.3)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#53627A',
        formatter: (val: number) => `${val > 0 ? `+${val}` : val}%`,
        fontSize: 10,
      },
      splitLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.15)' } },
    },
    series: [
      {
        name: 'Daily Abnormal Return (AR)',
        type: 'bar',
        data: arValues.map((val) => ({
          value: val,
          itemStyle: {
            color: val >= 0 ? '#1246B3' : '#53627A',
            borderRadius: val >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3],
          },
        })),
        barMaxWidth: 18,
      },
    ],
  };
}

export function buildHeatmapOption(heatmap: EventStudyHeatmapResponse): EChartsOption {
  const yLabels: string[] = [];
  const rowsByLabel = new Map<string, Map<string, number>>();

  heatmap.election_types.forEach((type) => {
    heatmap.stages.forEach((st) => {
      const label = `${type} — ${st.replace('_', ' ')}`;
      yLabels.push(label);
      rowsByLabel.set(label, new Map());
    });
  });

  const cellsData: [number, number, number, number, boolean][] = [];

  heatmap.cells.forEach((cell) => {
    const label = `${cell.election_type} — ${cell.stage.replace('_', ' ')}`;
    const yIdx = yLabels.indexOf(label);
    const xIdx = heatmap.windows.indexOf(cell.window);

    if (xIdx !== -1 && yIdx !== -1) {
      cellsData.push([xIdx, yIdx, cell.caar, cell.t_pval_bh ?? 1, (cell.t_pval_bh ?? 1) < 0.05]);
    }
  });

  return {
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(10, 42, 102, 0.95)',
      borderColor: '#1246B3',
      textStyle: { color: '#FFFFFF', fontSize: 12 },
      formatter: (params: unknown) => {
        const p = params as { data: [number, number, number, number, boolean] };
        const [xIdx, yIdx, caar, pvalBh, isSig] = p.data;
        const win = heatmap.windows[xIdx];
        const group = yLabels[yIdx];
        return `
          <div class="font-bold border-b border-white/20 pb-1 mb-1">${group}</div>
          <div class="flex justify-between gap-4"><span>Window:</span><span class="font-mono">${win}</span></div>
          <div class="flex justify-between gap-4"><span>Mean CAAR:</span><span class="font-mono font-bold">${caar > 0 ? `+${caar}` : caar}%</span></div>
          <div class="flex justify-between gap-4"><span>FDR BH p-val:</span><span class="font-mono">${pvalBh} ${isSig ? '(**)' : ''}</span></div>
        `;
      },
    },
    grid: { left: 160, right: 30, top: 20, bottom: 65 },
    xAxis: {
      type: 'category',
      data: heatmap.windows,
      axisLabel: { color: '#53627A', fontSize: 10, rotate: 30 },
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      axisLabel: { color: '#53627A', fontSize: 10 },
      splitArea: { show: true },
    },
    visualMap: {
      min: -5,
      max: 5,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 5,
      inRange: {
        color: ['#0A2A66', '#3563C1', '#EDF2FB', '#00B8D9', '#0095B3'],
      },
      textStyle: { color: '#53627A', fontSize: 11 },
    },
    series: [
      {
        name: 'Average CAAR',
        type: 'heatmap',
        data: cellsData.map((d) => [d[0], d[1], d[2]]),
        label: {
          show: true,
          formatter: (params: unknown) => {
            const p = params as { data: [number, number, number] };
            const val = p.data[2];
            return `${val > 0 ? `+${val}` : val}%`;
          },
          fontSize: 9,
          color: '#1E293B',
        },
      },
    ],
  };
}

export function buildForestPlotOption(items: EventStudyPerEventItem[]): EChartsOption {
  const shortNames = items.map((it) => {
    const cleanType = it.election_type.replace('Sri Lankan ', '');
    return `${it.year} ${cleanType}`;
  });
  const cars = items.map((it, idx) => [it.car, idx]);
  const linesData = items.map((it, idx) => ({
    coords: [
      [it.ci_lower, idx],
      [it.ci_upper, idx],
    ],
  }));

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(10, 42, 102, 0.95)',
      borderColor: '#1246B3',
      textStyle: { color: '#FFFFFF', fontSize: 12 },
      formatter: (params: unknown) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const idx = params[0].dataIndex;
        const it = items[idx];
        return `
          <div class="font-bold border-b border-white/20 pb-1 mb-1">${it.event_name}</div>
          <div class="flex justify-between gap-4"><span>CAR:</span><span class="font-mono font-bold">${it.car > 0 ? `+${it.car}` : it.car}%</span></div>
          <div class="flex justify-between gap-4 text-xs text-white/70"><span>95% CI:</span><span class="font-mono">[${it.ci_lower}%, ${it.ci_upper}%]</span></div>
          <div class="flex justify-between gap-4 text-xs text-white/70"><span>p-value:</span><span class="font-mono">${it.p_value} (BH: ${it.corrected_p_val})</span></div>
        `;
      },
    },
    grid: { left: 130, right: 25, top: 20, bottom: 25, containLabel: false },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#53627A',
        formatter: (val: number) => `${val > 0 ? `+${val}` : val}%`,
        fontSize: 10,
      },
      splitLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.15)' } },
    },
    yAxis: {
      type: 'category',
      data: shortNames,
      axisLabel: { color: '#53627A', fontSize: 10 },
      inverse: true,
    },
    series: [
      {
        name: '95% Confidence Interval',
        type: 'lines',
        coordinateSystem: 'cartesian2d',
        data: linesData,
        lineStyle: {
          color: '#3563C1',
          width: 2,
        },
        z: 2,
      },
      {
        name: 'CAR (%)',
        type: 'scatter',
        data: cars,
        symbolSize: 7,
        itemStyle: { color: '#0A2A66' },
        markLine: {
          data: [{ xAxis: 0, lineStyle: { color: '#0095B3', type: 'dashed' } }],
        },
        z: 3,
      },
    ],
  };
}

export function buildPermutationHistogramOption(
  distribution?: PermutationDistribution
): EChartsOption {
  if (!distribution) return {};

  const bins = distribution.bins;
  const labels = bins.map((b) => `${b.min}%`);
  const counts = bins.map((b) => b.count);
  const obs = distribution.observed_value;

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 42, 102, 0.95)',
      borderColor: '#1246B3',
      textStyle: { color: '#FFFFFF', fontSize: 12 },
    },
    grid: { left: 45, right: 25, top: 30, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#53627A', fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.3)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#53627A', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(83, 98, 122, 0.15)' } },
    },
    series: [
      {
        name: 'Placebo Permutation Frequency (H0)',
        type: 'bar',
        data: counts,
        itemStyle: { color: 'rgba(18, 70, 179, 0.45)', borderRadius: [2, 2, 0, 0] },
        barMaxWidth: 16,
        markLine: {
          symbol: ['none', 'none'],
          data: [
            {
              xAxis: `${Math.round(obs * 2) / 2}%`,
              lineStyle: { color: '#0095B3', width: 2.5, type: 'solid' },
              label: {
                formatter: `Observed: ${obs > 0 ? `+${obs}` : obs}% (p=${distribution.p_value})`,
                position: 'insideEndTop',
                color: '#0095B3',
                fontSize: 11,
              },
            },
          ],
        },
      },
    ],
  };
}
