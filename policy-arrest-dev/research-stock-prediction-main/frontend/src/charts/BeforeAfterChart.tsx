import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { PricePathPoint } from '../types';

interface BeforeAfterChartProps {
  pricePath: PricePathPoint[];
  height?: string;
  title?: string;
}

export const BeforeAfterChart: React.FC<BeforeAfterChartProps> = ({ pricePath, height = '280px', title }) => {
  const option = useMemo(() => {
    if (!pricePath || pricePath.length === 0) return {};

    const days = pricePath.map((p) => (p.relative_day === 0 ? 't0 (Event)' : `t${p.relative_day > 0 ? '+' : ''}${p.relative_day}`));
    const returns = pricePath.map((p) => p.pct_change_from_event);

    return {
      backgroundColor: 'transparent',
      title: title ? { text: title, textStyle: { color: '#0F172A', fontSize: 13, fontWeight: 'bold' } } : undefined,
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#FFFFFF',
        borderColor: '#CBD5E1',
        borderWidth: 1,
        extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;',
        textStyle: { color: '#0F172A', fontSize: 12 },
        formatter: (params: any[]) => {
          if (!params || !params.length) return '';
          const idx = params[0].dataIndex;
          const pt = pricePath[idx];
          return `
            <div>
              <div style="font-weight:bold; color:#0F172A;">${pt.relative_day === 0 ? 'Event Announcement Day' : `Session ${pt.relative_day}`}</div>
              <div style="font-size:11px; color:#64748B;">Date: ${pt.date}</div>
              <div style="font-size:13px; font-weight:bold; margin-top:4px; color:${pt.pct_change_from_event >= 0 ? '#16A34A' : '#DC2626'};">
                Change: ${pt.pct_change_from_event > 0 ? '+' : ''}${pt.pct_change_from_event}%
              </div>
              <div style="font-size:11px; color:#64748B;">ASPI Close: ${pt.aspi_close.toLocaleString()}</div>
            </div>
          `;
        }
      },
      grid: {
        left: '4%',
        right: '4%',
        bottom: '12%',
        top: title ? '18%' : '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: days,
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#64748B', fontSize: 10, interval: 2 }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        splitLine: { lineStyle: { color: '#F1F5F9' } },
        axisLabel: {
          color: '#64748B',
          fontSize: 10,
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: '% Change from Event Close',
          type: 'line',
          data: returns,
          smooth: true,
          lineStyle: { color: '#2563EB', width: 2.5 },
          showSymbol: false,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(37, 99, 235, 0.18)' },
                { offset: 1, color: 'rgba(37, 99, 235, 0.0)' }
              ]
            }
          },
          markLine: {
            silent: true,
            symbol: 'none',
            data: [
              {
                xAxis: pricePath.findIndex((p) => p.relative_day === 0),
                lineStyle: { color: '#D97706', type: 'dashed', width: 2 },
                label: { show: true, formatter: 'Event Day (t0)', position: 'insideEndTop', color: '#D97706', fontWeight: 'bold' }
              },
              {
                yAxis: 0,
                lineStyle: { color: '#94A3B8', type: 'solid', width: 1 }
              }
            ]
          }
        }
      ]
    };
  }, [pricePath, title]);

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} />
    </div>
  );
};
