import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { StockPoint, EventMarker } from '../types';

interface TimelineChartProps {
  priceSeries: StockPoint[];
  eventMarkers: EventMarker[];
  onSelectEvent?: (eventId: string) => void;
  height?: string;
}

export const TimelineChart: React.FC<TimelineChartProps> = ({
  priceSeries,
  eventMarkers,
  onSelectEvent,
  height = '480px'
}) => {
  const option = useMemo(() => {
    const dates = priceSeries.map((p) => p.date);
    const aspiValues = priceSeries.map((p) => p.aspi);

    // Map events to markPoints (Blue for Policies, Amber-Gold for Arrests)
    const markPointData = eventMarkers.map((em) => {
      const isPolicy = em.event_family === 'Government Policy';
      const isPositive = em.car_5d > 0;
      
      return {
        name: em.title,
        eventId: em.event_id,
        coord: [em.aligned_date, em.aspi_close_event],
        value: isPolicy ? 'P' : 'A',
        symbol: isPolicy ? 'diamond' : 'pin',
        symbolSize: isPolicy ? 18 : 22,
        itemStyle: {
          color: isPolicy ? '#2563EB' : '#D97706',
          borderColor: isPositive ? '#16A34A' : '#DC2626',
          borderWidth: 2,
          shadowBlur: 4,
          shadowColor: 'rgba(0,0,0,0.15)'
        },
        label: {
          show: true,
          formatter: isPolicy ? 'POL' : 'ARR',
          fontSize: 9,
          fontWeight: 'bold',
          color: '#FFFFFF'
        },
        tooltipData: em
      };
    });

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#FFFFFF',
        borderColor: '#CBD5E1',
        borderWidth: 1,
        extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;',
        textStyle: { color: '#0F172A' },
        formatter: (params: any) => {
          if (!params || !params.length) return '';
          const p = params[0];
          const dateStr = p.axisValue;
          const val = p.value;

          // Check if there is an event on this date
          const eventsOnDate = eventMarkers.filter((e) => e.aligned_date === dateStr);
          let extraHtml = '';
          if (eventsOnDate.length > 0) {
            extraHtml = eventsOnDate
              .map(
                (ev) => `
              <div style="margin-top:6px; padding-top:6px; border-top:1px solid #E2E8F0;">
                <span style="font-weight:bold; color:${ev.event_family === 'Government Policy' ? '#2563EB' : '#D97706'}">
                  [${ev.event_family === 'Government Policy' ? 'POLICY' : 'ARREST'}] ${ev.title}
                </span><br/>
                <span style="color:#64748B; font-size:11px;">Category: ${ev.event_subtype}</span><br/>
                <span style="color:${ev.car_5d >= 0 ? '#16A34A' : '#DC2626'}; font-weight:bold;">
                  5-Day CAR: ${ev.car_5d > 0 ? '+' : ''}${ev.car_5d}% (${ev.impact_direction})
                </span><br/>
                <span style="font-size:10px; color:#2563EB;">Click marker for complete trajectory</span>
              </div>`
              )
              .join('');
          }

          return `
            <div style="font-family:Inter, sans-serif; font-size:12px;">
              <div style="color:#64748B; margin-bottom:4px;">Session: ${dateStr}</div>
              <div style="font-size:14px; font-weight:bold; color:#0F172A;">ASPI Close: ${val ? val.toLocaleString() : 'N/A'}</div>
              ${extraHtml}
            </div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '14%',
        top: '6%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#64748B', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitLine: { lineStyle: { color: '#F1F5F9' } },
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#64748B', fontSize: 11 }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          borderColor: '#E2E8F0',
          fillerColor: 'rgba(37, 99, 235, 0.12)',
          textStyle: { color: '#64748B' },
          bottom: '2%'
        }
      ],
      series: [
        {
          name: 'ASPI',
          type: 'line',
          data: aspiValues,
          smooth: true,
          showSymbol: false,
          lineStyle: {
            color: '#2563EB',
            width: 2.5
          },
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
          markPoint: {
            data: markPointData
          }
        }
      ]
    };
  }, [priceSeries, eventMarkers]);

  const onChartClick = (params: any) => {
    if (params.componentType === 'markPoint' && params.data?.eventId) {
      onSelectEvent?.(params.data.eventId);
    }
  };

  return (
    <div className="w-full relative">
      <ReactECharts
        option={option}
        style={{ height, width: '100%' }}
        onEvents={{ click: onChartClick }}
        notMerge={true}
      />
    </div>
  );
};
