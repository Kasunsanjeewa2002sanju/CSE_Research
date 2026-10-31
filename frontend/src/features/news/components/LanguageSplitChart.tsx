import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { ChartCard } from '@/components/charts/ChartCard';
import type { LanguageSplitItem } from '../types';

export interface LanguageSplitChartProps {
  data: LanguageSplitItem[];
  isLoading?: boolean;
}

const LANG_COLORS: Record<string, string> = {
  en: '#1246B3', // cobalt
  si: '#E39B0B', // lion amber / Sinhala
  ta: '#D93A3A', // maroon red / Tamil
};

export function LanguageSplitChart({ data, isLoading = false }: LanguageSplitChartProps) {
  const chartOption = useMemo<EChartsOption>(() => {
    const pieData = data.map((item) => ({
      name: item.label,
      value: item.count,
      itemStyle: {
        color: LANG_COLORS[item.language] || '#64748B',
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
        bottom: 0,
        textStyle: { color: '#53627A', fontSize: 11 },
      },
      series: [
        {
          name: 'Language Distribution',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{d}%',
            fontSize: 11,
            color: '#0B1B33',
          },
          data: pieData,
        },
      ],
    };
  }, [data]);

  // Data table fallback representation for WCAG 2.1 AA accessibility per Rule FR6
  const dataTableData = useMemo(() => {
    return data.map((d) => ({
      language: d.label,
      code: d.language.toUpperCase(),
      count: d.count,
      percentage: `${d.percentage}%`,
    }));
  }, [data]);

  const dataTableColumns = useMemo(
    () => [
      { key: 'language', header: 'Language', sortable: true },
      { key: 'code', header: 'ISO Code', sortable: true },
      { key: 'count', header: 'Articles Ingested', sortable: true },
      { key: 'percentage', header: 'Share %', sortable: true },
    ],
    []
  );

  return (
    <ChartCard
      title="Language Distribution"
      subtitle="Multilingual natural language coverage across Sri Lankan news publications."
      infoTooltip="Real-time share of ingested articles written in English, Sinhala, and Tamil."
      option={chartOption}
      dataTableData={dataTableData}
      dataTableColumns={dataTableColumns}
      isLoading={isLoading}
      isEmpty={data.length === 0}
      height={300}
    />
  );
}
export default LanguageSplitChart;
