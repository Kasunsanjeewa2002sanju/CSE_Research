import type { LineSeriesOption } from 'echarts';

export interface ConfidenceBandDataPoint {
  x: string | number;
  median: number;
  lower: number;
  upper: number;
}

/**
 * Creates ECharts stacked area series to render 80% or 95% confidence intervals.
 * Uses stack arithmetic: base series (lower) + difference series (upper - lower).
 */
export function createConfidenceBandSeries(
  data: ConfidenceBandDataPoint[],
  options?: {
    medianName?: string;
    bandName?: string;
    bandColor?: string;
    medianColor?: string;
  }
): LineSeriesOption[] {
  const medianName = options?.medianName || 'Point Estimate';
  const bandName = options?.bandName || '95% Confidence Interval';
  const bandColor = options?.bandColor || 'rgba(27, 92, 214, 0.14)';
  const medianColor = options?.medianColor || '#1B5CD6';

  const lowerData = data.map((d) => d.lower);
  const diffData = data.map((d) => d.upper - d.lower);
  const medianData = data.map((d) => d.median);

  return [
    // 1. Lower Bound Base (Invisible)
    {
      name: `${bandName} (Lower)`,
      type: 'line',
      data: lowerData,
      lineStyle: { opacity: 0 },
      stack: `confidence-band-${bandName}`,
      symbol: 'none',
      silent: true,
    },
    // 2. Shaded Confidence Ribbon (Upper - Lower)
    {
      name: bandName,
      type: 'line',
      data: diffData,
      lineStyle: { opacity: 0 },
      areaStyle: {
        color: bandColor,
      },
      stack: `confidence-band-${bandName}`,
      symbol: 'none',
      smooth: true,
    },
    // 3. Central Median Trajectory
    {
      name: medianName,
      type: 'line',
      data: medianData,
      lineStyle: {
        color: medianColor,
        width: 2.5,
      },
      itemStyle: {
        color: medianColor,
      },
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
    },
  ];
}

/**
 * Creates a vertical MarkLine for key political events (e.g. t = 0 event date).
 */
export function createEventMarkLine(
  xCoord: string | number,
  label = 'Event Date (t = 0)',
  color = '#D93A3A'
) {
  return {
    symbol: ['none', 'none'],
    silent: false,
    lineStyle: {
      color,
      type: 'dashed' as const,
      width: 1.5,
    },
    label: {
      formatter: label,
      position: 'insideEndTop' as const,
      color,
      fontSize: 10,
      fontFamily: '"JetBrains Mono", monospace',
    },
    data: [{ xAxis: xCoord }],
  };
}

/**
 * Creates a shaded MarkArea for event windows (e.g. [-14, +14] trading days).
 */
export function createEventWindowMarkArea(
  startX: string | number,
  endX: string | number,
  label = 'Event Window',
  color = 'rgba(227, 155, 11, 0.08)'
) {
  return {
    silent: true,
    itemStyle: {
      color,
    },
    label: {
      show: true,
      position: 'insideTopLeft' as const,
      color: '#E39B0B',
      fontSize: 10,
      fontFamily: '"JetBrains Mono", monospace',
      formatter: label,
    },
    data: [[{ xAxis: startX }, { xAxis: endX }]],
  };
}
