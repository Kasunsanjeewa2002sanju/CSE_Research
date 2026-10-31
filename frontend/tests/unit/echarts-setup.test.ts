import { describe, it, expect } from 'vitest';
import { echarts } from '@/components/charts/echarts-setup';
import {
  createPriceOption,
  createReturnsOption,
  createVolatilityOption,
  createVolumeOption,
} from '@/features/data-explorer/utils/chart-options';
import { createTradingDaysOption } from '@/features/data-explorer/utils/audit-helpers';

describe('ECharts Tree-Shaking Setup & Component Registration', () => {
  it('registers all required core modules, components, and renderers without runtime failure', () => {
    expect(echarts).toBeDefined();
    expect(typeof echarts.init).toBe('function');
    expect(typeof echarts.use).toBe('function');
    expect(echarts.graphic).toBeDefined();
    expect(typeof echarts.graphic.LinearGradient).toBe('function');
  });

  it('correctly maps linear scaleType to value axis type to avoid yAxis.linear registration errors', () => {
    const linearOpt = createPriceOption({
      filteredPoints: [{ date: '2024-01-01', aspi: 10000, turnover: 1000000, volume: 50000 }],
      normalizedSp: [],
      showSpSl20: false,
      scaleType: 'linear',
      electionMarkLines: [],
    });

    const logOpt = createPriceOption({
      filteredPoints: [{ date: '2024-01-01', aspi: 10000, turnover: 1000000, volume: 50000 }],
      normalizedSp: [],
      showSpSl20: false,
      scaleType: 'log',
      electionMarkLines: [],
    });

    // In ECharts, Cartesian numerical linear axes are 'value', not 'linear'
    expect((linearOpt.yAxis as Record<string, unknown>).type).toBe('value');
    expect((logOpt.yAxis as Record<string, unknown>).type).toBe('log');
  });

  it('generates valid price option with grid, tooltip, legend, and dataZoom components', () => {
    const opt = createPriceOption({
      filteredPoints: [
        { date: '2024-01-01', aspi: 10000, turnover: 1000000, volume: 50000 },
        { date: '2024-01-02', aspi: 10050, turnover: 1100000, volume: 55000 },
      ],
      normalizedSp: [{ date: '2024-01-01', normalized: 10000 }],
      showSpSl20: true,
      scaleType: 'linear',
      electionMarkLines: [
        {
          xAxis: '2024-01-01',
          label: { formatter: 'Election' },
          lineStyle: { color: '#E39B0B' },
        },
      ],
    });

    expect(opt.grid).toBeDefined();
    expect(opt.tooltip).toBeDefined();
    expect(opt.legend).toBeDefined();
    expect(opt.dataZoom).toBeDefined();
    expect(opt.xAxis).toBeDefined();
    expect(opt.yAxis).toBeDefined();
    expect(opt.series).toHaveLength(2); // ASPI + S&P SL 20
  });

  it('generates valid returns, volatility, volume, and trading days options', () => {
    const points = [
      { date: '2024-01-01', aspi: 10000, return: 0.005, turnover: 5000000, volume: 100000 },
      { date: '2024-01-02', aspi: 10050, return: -0.002, turnover: 4500000, volume: 90000 },
    ];

    const returnsOpt = createReturnsOption(points);
    expect(returnsOpt.series).toBeDefined();
    expect((returnsOpt.xAxis as Record<string, unknown>).type).toBe('category');

    const volOpt = createVolatilityOption({
      rollingVol: [{ date: '2024-01-01', volatility: 15.5 }],
      volatilityWindow: 20,
    });
    expect(volOpt.series).toBeDefined();

    const volmOpt = createVolumeOption(points);
    expect(volmOpt.series).toHaveLength(2);

    const auditDaysOpt = createTradingDaysOption([
      { year: 2024, trading_days: 242, expected: 240 },
    ]);
    expect(auditDaysOpt.series).toBeDefined();
  });

  it('instantiates an ECharts instance without throwing component registration errors', () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'clientWidth', { value: 600, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 400, configurable: true });
    document.body.appendChild(container);

    const chart = echarts.init(container, null, {
      renderer: 'canvas',
      width: 600,
      height: 400,
    });
    expect(chart).toBeDefined();

    const option = createPriceOption({
      filteredPoints: [{ date: '2024-01-01', aspi: 10000, turnover: 1000000, volume: 50000 }],
      normalizedSp: [],
      showSpSl20: false,
      scaleType: 'linear',
      electionMarkLines: [],
    });

    expect(() => {
      chart.setOption(option);
    }).not.toThrow();

    chart.dispose();
    document.body.removeChild(container);
  });
});
