import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { ChartCard } from '@/components/charts/ChartCard';
import type { ClassificationDistributionItem } from '../types';

export interface ClassificationDistributionChartProps {
  data: ClassificationDistributionItem[];
  isLoading?: boolean;
}

const CATEGORY_COLORS = [
  '#0A2A66', // navy
  '#1246B3', // cobalt
  '#00B8D9', // cyan
  '#0F9D6B', // green
  '#E39B0B', // amber
  '#D93A3A', // red
  '#7C3AED', // purple
  '#64748B', // slate
];

export function ClassificationDistributionChart({
  data,
  isLoading = false,
}: ClassificationDistributionChartProps) {
  const chartOption = useMemo<EChartsOption>(() => {
    const pieData = data.map((item, idx) => ({
      name: item.label || item.category,
      value: item.count,
      itemStyle: {
        color: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
      },
    }));

    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: <strong>{c} articles</strong> ({d}%)',
        backgroundColor: '#0A2A66',
        borderColor: '#00B8D9',
        textStyle: { color: '#FFFFFF', fontSize: 11 },
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        textStyle: { color: '#53627A', fontSize: 11 },
        type: 'scroll',
      },
      series: [
        {
          name: 'News Event Category',
          type: 'pie',
          radius: ['45%', '72%'],
          center: ['38%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 13,
              fontWeight: 'bold',
              color: '#0B1B33',
            },
          },
          labelLine: { show: false },
          data: pieData,
        },
      ],
    };
  }, [data]);

  // Data table fallback representation for WCAG 2.1 AA accessibility per Rule FR6
  const dataTableData = useMemo(() => {
    return data.map((d) => ({
      category: d.label || d.category,
      count: d.count,
      percentage: `${d.percentage}%`,
    }));
  }, [data]);

  const dataTableColumns = useMemo(
    () => [
      { key: 'category', header: 'Event Category', sortable: true },
      { key: 'count', header: 'Articles Count', sortable: true },
      { key: 'percentage', header: 'Distribution %', sortable: true },
    ],
    []
  );

  return (
    <ChartCard
      title="News Classification Distribution"
      subtitle="Categorical breakdown of live Sri Lankan news items categorized by Stage 10 financial NLP."
      infoTooltip="Proportion of articles tagged as political, constitutional, macroeconomic, or unassociated."
      option={chartOption}
      dataTableData={dataTableData}
      dataTableColumns={dataTableColumns}
      isLoading={isLoading}
      isEmpty={data.length === 0}
      height={300}
    />
  );
}
export default ClassificationDistributionChart;
