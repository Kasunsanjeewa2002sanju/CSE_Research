import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { ChartCard } from '@/components/charts/ChartCard';
import type { ItemsPerHourItem } from '../types';

export interface ItemsPerHourChartProps {
  data: ItemsPerHourItem[];
  isLoading?: boolean;
}

const SOURCE_COLORS = [
  '#1246B3', // blue-cobalt
  '#00B8D9', // cyan accent
  '#0F9D6B', // green
  '#E39B0B', // amber
  '#7C3AED', // purple
  '#EC4899', // pink
  '#64748B', // slate
];

export function ItemsPerHourChart({ data, isLoading = false }: ItemsPerHourChartProps) {
  // Extract distinct sources across all hours
  const sources = useMemo(() => {
    const sSet = new Set<string>();
    data.forEach((item) => {
      Object.keys(item.by_source || {}).forEach((s) => sSet.add(s));
    });
    return Array.from(sSet).sort();
  }, [data]);

  const chartOption = useMemo<EChartsOption>(() => {
    const hours = data.map((d) => d.hour);

    const series = sources.map((src, idx) => {
      const color = SOURCE_COLORS[idx % SOURCE_COLORS.length];
      return {
        name: src,
        type: 'bar' as const,
        stack: 'total',
        emphasis: { focus: 'series' as const },
        itemStyle: { color },
        data: data.map((d) => d.by_source?.[src] || 0),
      };
    });

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#0A2A66',
        borderColor: '#00B8D9',
        textStyle: { color: '#FFFFFF', fontSize: 11 },
      },
      legend: {
        top: 0,
        textStyle: { color: '#53627A', fontSize: 11 },
        type: 'scroll',
      },
      grid: {
        top: 40,
        right: 16,
        bottom: 24,
        left: 48,
        containLabel: false,
      },
      xAxis: {
        type: 'category',
        data: hours,
        axisLine: { lineStyle: { color: '#E1E8F2' } },
        axisLabel: { color: '#53627A', fontSize: 10, interval: 2 },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#53627A', fontSize: 10 },
        splitLine: { lineStyle: { color: '#EEF3FA' } },
      },
      series,
    };
  }, [data, sources]);

  // Data table fallback representation for WCAG 2.1 AA accessibility per Rule FR6
  const dataTableData = useMemo(() => {
    return data.map((d) => {
      const row: Record<string, unknown> = {
        hour: d.hour,
        total: d.total,
      };
      sources.forEach((s) => {
        row[s] = d.by_source?.[s] || 0;
      });
      return row;
    });
  }, [data, sources]);

  const dataTableColumns = useMemo(() => {
    return [
      { key: 'hour', header: 'Hour (UTC)', sortable: true },
      { key: 'total', header: 'Total Ingested', sortable: true },
      ...sources.map((s) => ({ key: s, header: s, sortable: true })),
    ];
  }, [sources]);

  return (
    <ChartCard
      title="Items Ingested per Hour by Source (Last 24 Hours)"
      subtitle="Rolling hourly frequency distribution across active Sri Lankan RSS feeds and query scrapers."
      infoTooltip="Hourly volume of raw articles fetched, deduplicated, and passed into FinBERT sentiment pipeline."
      option={chartOption}
      dataTableData={dataTableData}
      dataTableColumns={dataTableColumns}
      isLoading={isLoading}
      isEmpty={data.length === 0}
      height={320}
    />
  );
}
export default ItemsPerHourChart;
