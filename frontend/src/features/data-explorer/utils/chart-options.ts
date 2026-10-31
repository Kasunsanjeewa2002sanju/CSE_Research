import { echarts, EChartsOption } from '@/components/charts';
import type { MarketDataPoint } from './market-calculations';

export interface PriceOptionParams {
  filteredPoints: MarketDataPoint[];
  normalizedSp: Array<{ date: string; normalized: number | null }>;
  showSpSl20: boolean;
  scaleType: 'linear' | 'log';
  electionMarkLines: Array<Record<string, unknown>>;
}

export function createPriceOption({
  filteredPoints,
  normalizedSp,
  showSpSl20,
  scaleType,
  electionMarkLines,
}: PriceOptionParams): EChartsOption {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', link: [{ xAxisIndex: 'all' }] },
    },
    legend: {
      data: showSpSl20 ? ['ASPI Index', 'S&P SL 20 (Normalised)'] : ['ASPI Index'],
      top: 0,
      right: 10,
    },
    grid: { left: '3%', right: '3%', bottom: '15%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: filteredPoints.map((p) => p.date),
      boundaryGap: false,
    },
    yAxis: {
      type: scaleType === 'log' ? 'log' : 'value',
      scale: true,
      splitLine: { show: true, lineStyle: { color: '#E1E8F2', type: 'dashed' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', bottom: 0, height: 20 },
    ],
    series: [
      {
        name: 'ASPI Index',
        type: 'line',
        data: filteredPoints.map((p) => p.aspi),
        smooth: false,
        symbol: 'none',
        lineStyle: { width: 2, color: '#1246B3' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(18, 70, 179, 0.28)' },
            { offset: 1, color: 'rgba(18, 70, 179, 0.01)' },
          ]),
        },
        markLine: {
          silent: false,
          symbol: ['none', 'none'],
          data: electionMarkLines,
        },
      },
      ...(showSpSl20
        ? [
            {
              name: 'S&P SL 20 (Normalised)',
              type: 'line' as const,
              data: normalizedSp.map((p) => p.normalized),
              smooth: false,
              symbol: 'none',
              lineStyle: { width: 1.75, color: '#00B8D9', type: 'solid' as const },
            },
          ]
        : []),
    ],
  };
}

export function createReturnsOption(filteredPoints: MarketDataPoint[]): EChartsOption {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '3%', bottom: '10%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: filteredPoints.map((p) => p.date),
      boundaryGap: true,
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    series: [
      {
        name: 'Daily Return',
        type: 'bar',
        data: filteredPoints.map((p) => {
          const val = (p.return ?? 0) * 100;
          return {
            value: Number(val.toFixed(2)),
            itemStyle: { color: val >= 0 ? '#0F9D6B' : '#D93A3A' },
          };
        }),
      },
    ],
  };
}

export interface VolatilityOptionParams {
  rollingVol: Array<{ date: string; volatility: number | null }>;
  volatilityWindow: number;
}

export function createVolatilityOption({
  rollingVol,
  volatilityWindow,
}: VolatilityOptionParams): EChartsOption {
  return {
    tooltip: { trigger: 'axis', valueFormatter: (val) => `${val}% (Ann.)` },
    grid: { left: '3%', right: '3%', bottom: '10%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rollingVol.map((p) => p.date),
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    series: [
      {
        name: `${volatilityWindow}D Annualized Volatility`,
        type: 'line',
        data: rollingVol.map((p) => p.volatility),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#00B8D9' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 184, 217, 0.25)' },
            { offset: 1, color: 'rgba(0, 184, 217, 0.01)' },
          ]),
        },
      },
    ],
  };
}

export function createVolumeOption(filteredPoints: MarketDataPoint[]): EChartsOption {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '3%', bottom: '10%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: filteredPoints.map((p) => p.date),
    },
    yAxis: [
      {
        type: 'value',
        name: 'Turnover (LKR)',
        axisLabel: { formatter: (v: number) => `${(v / 1e6).toFixed(0)}M` },
      },
      {
        type: 'value',
        name: 'Shares',
        position: 'right',
        axisLabel: { formatter: (v: number) => `${(v / 1e6).toFixed(0)}M` },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Turnover (LKR)',
        type: 'bar',
        data: filteredPoints.map((p) => p.turnover),
        itemStyle: { color: '#1B5CD6' },
      },
      {
        name: 'Shares Traded',
        type: 'line',
        yAxisIndex: 1,
        data: filteredPoints.map((p) => p.volume),
        itemStyle: { color: '#0A2A66' },
        symbol: 'none',
      },
    ],
  };
}
