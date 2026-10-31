import type { MarketSeriesPoint, PoliticalEvent } from '@/api/types';
import type { EChartsOption } from 'echarts';
import { getEventTypeColor } from './timeline-helpers';

export interface AlignedPathPoint {
  relativeDay: number; // -20 to +20
  tradingDate: string;
  aspiLevel: number;
  normalizedLevel: number; // 100.0 at t=0
  cumulativeReturnPct: number; // percentage from t=0
}

export interface AlignedEventPath {
  event: PoliticalEvent;
  reactionDate: string;
  reactionAspi: number;
  points: AlignedPathPoint[];
  carMinus3Plus3: number;
  carMinus1Plus1: number;
  sampleDays: number;
}

/**
 * Aligns ASPI price trajectory for an event around its mapped reaction date (t=0).
 */
export function alignAspiPath(
  event: PoliticalEvent,
  fullSeries: MarketSeriesPoint[],
  windowRadius = 20
): AlignedEventPath | null {
  if (!fullSeries || fullSeries.length === 0) return null;

  // Use mapped reaction date or event date
  const targetDate = event.mapped_date || event.mappedTradingDate || event.date;
  if (!targetDate) return null;

  // Find index in chronological series
  const eventIdx = fullSeries.findIndex((pt) => pt.date >= targetDate);
  if (eventIdx === -1) return null;

  const eventPoint = fullSeries[eventIdx];
  const reactionAspi = eventPoint.aspi;
  if (!reactionAspi || reactionAspi <= 0) return null;

  const alignedPoints: AlignedPathPoint[] = [];

  const startIdx = Math.max(0, eventIdx - windowRadius);
  const endIdx = Math.min(fullSeries.length - 1, eventIdx + windowRadius);

  for (let i = startIdx; i <= endIdx; i++) {
    const pt = fullSeries[i];
    const relativeDay = i - eventIdx;
    const normalized = (pt.aspi / reactionAspi) * 100;
    const cumulativeReturn = ((pt.aspi - reactionAspi) / reactionAspi) * 100;

    alignedPoints.push({
      relativeDay,
      tradingDate: pt.date,
      aspiLevel: pt.aspi,
      normalizedLevel: Math.round(normalized * 100) / 100,
      cumulativeReturnPct: Math.round(cumulativeReturn * 100) / 100,
    });
  }

  // Calculate CAR[-3, +3] and CAR[-1, +1]
  const pMinus3 = alignedPoints.find((p) => p.relativeDay === -3);
  const pPlus3 = alignedPoints.find((p) => p.relativeDay === 3);
  const pMinus1 = alignedPoints.find((p) => p.relativeDay === -1);
  const pPlus1 = alignedPoints.find((p) => p.relativeDay === 1);

  const carMinus3Plus3 =
    pMinus3 && pPlus3 && pMinus3.aspiLevel > 0
      ? Math.round(((pPlus3.aspiLevel - pMinus3.aspiLevel) / pMinus3.aspiLevel) * 10000) / 100
      : 0;

  const carMinus1Plus1 =
    pMinus1 && pPlus1 && pMinus1.aspiLevel > 0
      ? Math.round(((pPlus1.aspiLevel - pMinus1.aspiLevel) / pMinus1.aspiLevel) * 10000) / 100
      : 0;

  return {
    event,
    reactionDate: eventPoint.date,
    reactionAspi,
    points: alignedPoints,
    carMinus3Plus3,
    carMinus1Plus1,
    sampleDays: alignedPoints.length,
  };
}

/**
 * Builds an ECharts option comparing aligned event paths at t=0.
 */
export function createCompareChartOption(alignedPaths: AlignedEventPath[]): EChartsOption {
  const days = Array.from({ length: 41 }, (_, i) => i - 20); // -20 to +20

  const series = alignedPaths.map((ap, index) => {
    const colorPalette = getEventTypeColor(ap.event.category);
    // Distinct stroke styles for multiple events
    const lineStyles = [
      { color: colorPalette.primary, width: 2.5 },
      { color: '#1B5CD6', width: 2, type: 'dashed' as const },
      { color: '#0095B3', width: 2, type: 'dotted' as const },
    ];
    const style = lineStyles[index % lineStyles.length];

    const dataMap = new Map(ap.points.map((p) => [p.relativeDay, p.normalizedLevel]));
    const data = days.map((d) => dataMap.get(d) ?? null);

    return {
      name: ap.event.name,
      type: 'line' as const,
      smooth: true,
      data,
      lineStyle: style,
      symbol: 'circle',
      symbolSize: (_val: unknown, params: { dataIndex: number }) =>
        days[params.dataIndex] === 0 ? 8 : 4,
      emphasis: {
        focus: 'series' as const,
        lineStyle: { width: 3.5 },
      },
    };
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
          day === 0 ? 'Reaction Date (t = 0)' : `t = ${day > 0 ? `+${day}` : day} Trading Days`;
        let html = `<div class="font-bold mb-1">${dayLabel}</div>`;
        for (const item of params) {
          if (item.value !== null && item.value !== undefined) {
            const val = Number(item.value);
            const returnPct = Math.round((val - 100) * 100) / 100;
            const sign = returnPct >= 0 ? '+' : '';
            html += `<div style="display:flex; justify-content:space-between; gap:12px; margin-top:2px;">
              <span><span style="color:${item.color}">●</span> ${item.seriesName}:</span>
              <span class="font-mono"><strong>${val.toFixed(2)}</strong> (${sign}${returnPct.toFixed(2)}%)</span>
            </div>`;
          }
        }
        return html;
      },
    },
    legend: {
      data: alignedPaths.map((p) => p.event.name),
      bottom: 0,
      textStyle: { color: '#53627A', fontSize: 11 },
      type: 'scroll',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '12%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: days.map((d) => (d === 0 ? 't=0' : `${d > 0 ? `+${d}` : d}`)),
      axisLine: { lineStyle: { color: '#E1E8F2' } },
      axisLabel: { color: '#53627A', fontSize: 10, interval: 4 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      name: 'Normalized ASPI (t=0 at 100.0)',
      nameTextStyle: { color: '#53627A', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E1E8F2' } },
      axisLabel: {
        color: '#53627A',
        fontSize: 10,
        formatter: (val: number) => `${val.toFixed(0)}`,
      },
      splitLine: { lineStyle: { color: '#EEF3FA' } },
    },
    series: [
      ...series,
      {
        name: 'Event Horizon (t=0)',
        type: 'line',
        data: [],
        markLine: {
          symbol: ['none', 'none'],
          silent: true,
          data: [{ xAxis: 't=0' }],
          lineStyle: {
            color: '#00B8D9',
            type: 'solid',
            width: 1.5,
          },
          label: {
            formatter: 'Reaction (t=0)',
            position: 'insideStartTop',
            fontSize: 10,
            color: '#0095B3',
          },
        },
      },
    ],
  };
}
