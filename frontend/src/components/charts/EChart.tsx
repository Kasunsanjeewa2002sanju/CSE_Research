import React, { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { echarts } from './echarts-setup';
import type { ECharts, EChartsOption } from './echarts-setup';
import './echarts-theme';
import { CSE_RESEARCH_THEME_NAME } from './echarts-theme';

export interface EChartProps {
  option: EChartsOption;
  style?: React.CSSProperties;
  height?: string | number;
  width?: string | number;
  className?: string;
  loading?: boolean;
  onEvents?: Record<string, (params: unknown) => void>;
}

export interface EChartRef {
  getInstance: () => ECharts | null;
  exportToPng: () => string | null;
}

export const EChart = forwardRef<EChartRef, EChartProps>(
  ({ option, style, height = 320, width = '100%', className, loading = false, onEvents }, ref) => {
    const chartRef = useRef<HTMLDivElement>(null);
    const chartInstance = useRef<ECharts | null>(null);

    const mergedStyle: React.CSSProperties = {
      height,
      width,
      ...style,
    };

    useImperativeHandle(ref, () => ({
      getInstance: () => chartInstance.current,
      exportToPng: () => {
        if (!chartInstance.current) return null;
        return chartInstance.current.getDataURL({
          type: 'png',
          pixelRatio: 2,
          backgroundColor: '#FFFFFF',
        });
      },
    }));

    // Initialize chart
    useEffect(() => {
      if (!chartRef.current) return;

      const chart = echarts.init(chartRef.current, CSE_RESEARCH_THEME_NAME, {
        renderer: 'canvas',
      });
      chartInstance.current = chart;

      // Event listeners
      if (onEvents) {
        Object.entries(onEvents).forEach(([eventName, handler]) => {
          chart.on(eventName, handler);
        });
      }

      // Responsive resize observer
      const resizeObserver = new ResizeObserver(() => {
        chart.resize();
      });
      resizeObserver.observe(chartRef.current);

      return () => {
        resizeObserver.disconnect();
        chart.dispose();
        chartInstance.current = null;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Update options when memoized option prop changes
    useEffect(() => {
      if (!chartInstance.current) return;
      chartInstance.current.setOption(option, true);
    }, [option]);

    // Loading overlay
    useEffect(() => {
      if (!chartInstance.current) return;
      if (loading) {
        chartInstance.current.showLoading('default', {
          text: 'Loading series...',
          color: '#1B5CD6',
          textColor: '#53627A',
          maskColor: 'rgba(255, 255, 255, 0.7)',
        });
      } else {
        chartInstance.current.hideLoading();
      }
    }, [loading]);

    return <div ref={chartRef} style={mergedStyle} className={className} />;
  }
);

EChart.displayName = 'EChart';
