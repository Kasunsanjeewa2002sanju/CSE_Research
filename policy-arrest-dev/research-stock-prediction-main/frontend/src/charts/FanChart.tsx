import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { FanChartData } from '../types';

interface FanChartProps {
  data: FanChartData;
  height?: string;
  title?: string;
}

export const FanChart: React.FC<FanChartProps> = ({ data, height = '400px', title }) => {
  const option = useMemo(() => {
    if (!data || !data.forecast_path) return {};

    const histDates = data.pre_history.map((p) => p.date);
    const histPrices = data.pre_history.map((p) => p.actual_close);

    const forecastDates = data.forecast_path.map((p) => p.date);
    const allDates = [...histDates, ...forecastDates];

    // Pre-history padding with nulls for forecast series
    const histSeriesData = [...histPrices, ...Array(forecastDates.length).fill(null)];

    // Forecast series padded with nulls for history
    const padHist = Array(histDates.length - 1).fill(null);
    const lastHistPrice = histPrices[histPrices.length - 1];

    const centralPath = [...padHist, lastHistPrice, ...data.forecast_path.map((p) => p.event_predicted_central)];
    const baselinePath = [...padHist, lastHistPrice, ...data.forecast_path.map((p) => p.baseline_no_event)];

    // Bands for 95% and 80% (using lower bound and upper diff for stacked area)
    const lower95 = [...padHist, lastHistPrice, ...data.forecast_path.map((p) => p.lower_95)];
    const band95Diff = [...padHist, 0, ...data.forecast_path.map((p) => p.upper_95 - p.lower_95)];

    // Actual ground truth if present
    const actualSubsequent = [...padHist, lastHistPrice, ...data.forecast_path.map((p) => p.actual_subsequent_close ?? null)];

    return {
      backgroundColor: 'transparent',
      title: title ? { text: title, textStyle: { color: '#0F172A', fontSize: 14, fontWeight: 'bold' } } : undefined,
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#FFFFFF',
        borderColor: '#CBD5E1',
        borderWidth: 1,
        extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;',
        textStyle: { color: '#0F172A', fontSize: 12 },
        formatter: (params: any[]) => {
          if (!params || !params.length) return '';
          const date = params[0].axisValue;
          let html = `<div style="font-weight:bold; color:#0F172A; margin-bottom:4px;">${date}</div>`;
          params.forEach((item) => {
            if (item.value !== null && item.seriesName !== 'Band Base') {
              html += `<div style="font-size:11px; margin-top:2px;"><span style="color:${item.color};">●</span> ${item.seriesName}: <strong>${Math.round(item.value).toLocaleString()}</strong></div>`;
            }
          });
          return html;
        }
      },
      legend: {
        data: ['Historical Observed', 'Predicted Central Path', 'No-Event Baseline', '95% Uncertainty Band', 'Actual Post-Event Prices'],
        textStyle: { color: '#475569', fontSize: 11 },
        top: '2%'
      },
      grid: {
        left: '4%',
        right: '4%',
        bottom: '10%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: allDates,
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#64748B', fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitLine: { lineStyle: { color: '#F1F5F9' } },
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#64748B', fontSize: 10 }
      },
      series: [
        // 1. Historical Observed Line
        {
          name: 'Historical Observed',
          type: 'line',
          data: histSeriesData,
          smooth: true,
          lineStyle: { color: '#64748B', width: 2 },
          showSymbol: false
        },
        // 2. 95% Band Base (invisible)
        {
          name: 'Band Base',
          type: 'line',
          data: lower95,
          lineStyle: { opacity: 0 },
          stack: 'confidence-band-95',
          symbol: 'none'
        },
        // 3. 95% Band Area (stacked on base)
        {
          name: '95% Uncertainty Band',
          type: 'line',
          data: band95Diff,
          lineStyle: { opacity: 0 },
          areaStyle: { color: 'rgba(37, 99, 235, 0.12)' },
          stack: 'confidence-band-95',
          symbol: 'none'
        },
        // 4. No-Event Baseline (Dashed)
        {
          name: 'No-Event Baseline',
          type: 'line',
          data: baselinePath,
          smooth: true,
          lineStyle: { color: '#94A3B8', width: 2, type: 'dashed' },
          showSymbol: false
        },
        // 5. Predicted Central Path
        {
          name: 'Predicted Central Path',
          type: 'line',
          data: centralPath,
          smooth: true,
          lineStyle: { color: '#2563EB', width: 3 },
          showSymbol: false
        },
        // 6. Actual Ground Truth (if backtested)
        ...(data.has_actual_ground_truth
          ? [
              {
                name: 'Actual Post-Event Prices',
                type: 'line',
                data: actualSubsequent,
                smooth: true,
                lineStyle: { color: '#16A34A', width: 2.5 },
                showSymbol: false
              }
            ]
          : [])
      ]
    };
  }, [data, title]);

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} />
    </div>
  );
};
