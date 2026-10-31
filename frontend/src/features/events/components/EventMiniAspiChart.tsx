import { useEffect, useRef, useMemo } from 'react';
import { echarts } from '@/components/charts/echarts-setup';
import type { MarketSeriesPoint, PoliticalEvent } from '@/api/types';
import type { EChartsOption } from 'echarts';

export interface EventMiniAspiChartProps {
  event: PoliticalEvent;
  fullSeries: MarketSeriesPoint[];
  height?: number | string;
  className?: string;
}

export function EventMiniAspiChart({
  event,
  fullSeries,
  height = 240,
  className = '',
}: EventMiniAspiChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const windowData = useMemo(() => {
    if (!fullSeries || fullSeries.length === 0) return { dates: [], values: [], markLines: [] };

    const targetDate = event.mapped_date || event.mappedTradingDate || event.date;
    const eventIdx = fullSeries.findIndex((pt) => pt.date >= targetDate);
    if (eventIdx === -1) return { dates: [], values: [], markLines: [] };

    const radius = 25; // 25 trading days before and after
    const startIdx = Math.max(0, eventIdx - radius);
    const endIdx = Math.min(fullSeries.length - 1, eventIdx + radius);

    const slice = fullSeries.slice(startIdx, endIdx + 1);
    const dates = slice.map((pt) => pt.date);
    const values = slice.map((pt) => pt.aspi);

    // Map stages to markLines
    const markLines: {
      xAxis: string;
      label: { formatter: string };
      lineStyle: { color: string };
    }[] = [];
    if (event.stages && event.stages.length > 0) {
      for (const st of event.stages) {
        const sDate = st.mapped_date || st.date;
        if (dates.includes(sDate)) {
          markLines.push({
            xAxis: sDate,
            label: { formatter: st.stage_name },
            lineStyle: {
              color: st.stage_id.includes('poll') ? '#00B8D9' : '#1246B3',
            },
          });
        }
      }
    } else if (dates.includes(targetDate)) {
      markLines.push({
        xAxis: targetDate,
        label: { formatter: 'Polling (t=0)' },
        lineStyle: { color: '#00B8D9' },
      });
    }

    return { dates, values, markLines };
  }, [event, fullSeries]);

  const option = useMemo<EChartsOption>(() => {
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10, 42, 102, 0.95)',
        borderColor: '#1246B3',
        textStyle: { color: '#FFFFFF', fontSize: 11 },
        formatter: (params: unknown) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const pt = params[0];
          return `<div class="font-bold">${pt.axisValue}</div>
                  <div>ASPI: <span class="font-mono font-bold">${Number(pt.data).toLocaleString()}</span></div>`;
        },
      },
      grid: {
        left: '2%',
        right: '4%',
        bottom: '12%',
        top: '16%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: windowData.dates,
        axisLine: { lineStyle: { color: '#E1E8F2' } },
        axisLabel: {
          color: '#53627A',
          fontSize: 9,
          interval: Math.floor(windowData.dates.length / 5),
          formatter: (val: string) => val.slice(5), // MM-DD
        },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { lineStyle: { color: '#E1E8F2' } },
        axisLabel: {
          color: '#53627A',
          fontSize: 9,
          formatter: (val: number) => val.toLocaleString(),
        },
        splitLine: { lineStyle: { color: '#EEF3FA' } },
      },
      series: [
        {
          name: 'ASPI',
          type: 'line',
          data: windowData.values,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#1246B3', width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(27, 92, 214, 0.25)' },
              { offset: 1, color: 'rgba(27, 92, 214, 0.02)' },
            ]),
          },
          markLine: {
            symbol: ['none', 'none'],
            silent: true,
            data: windowData.markLines,
            label: {
              fontSize: 8,
              position: 'insideEndTop',
              color: '#0A2A66',
            },
          },
        },
      ],
    };
  }, [windowData]);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, null, { renderer: 'canvas' });
    }

    chartInstance.current.setOption(option);

    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, [option]);

  return (
    <div className={className}>
      <div
        ref={chartRef}
        style={{ width: '100%', height }}
        role="img"
        aria-label={`Mini ASPI index chart for ${event.name} with event stages`}
      />
    </div>
  );
}
