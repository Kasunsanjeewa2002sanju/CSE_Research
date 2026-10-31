import { describe, it, expect } from 'vitest';
import {
  normalizeSpSl20,
  calculateRollingVolatility,
  filterPointsByPreset,
  MarketDataPoint,
} from '@/features/data-explorer/utils/market-calculations';

describe('Stage F3: Data Explorer Market Calculations & Normalization', () => {
  const samplePoints: MarketDataPoint[] = [
    {
      date: '2012-06-15',
      aspi: 5000,
      sp_sl20: null,
      return: 0.01,
      turnover: 1000000,
      volume: 50000,
    },
    {
      date: '2012-06-18',
      aspi: 5020,
      sp_sl20: 2500,
      return: 0.004,
      turnover: 1100000,
      volume: 55000,
    },
    {
      date: '2012-06-19',
      aspi: 5100,
      sp_sl20: 2550,
      return: 0.016,
      turnover: 1200000,
      volume: 60000,
    },
    {
      date: '2012-06-20',
      aspi: 5050,
      sp_sl20: 2525,
      return: -0.01,
      turnover: 950000,
      volume: 48000,
    },
  ];

  it('correctly normalizes S&P SL 20 to base ASPI level at first valid point', () => {
    const normalized = normalizeSpSl20(samplePoints);

    expect(normalized).toHaveLength(4);
    // Before launch (null)
    expect(normalized[0].normalized).toBeNull();
    // At launch: (2500 / 2500) * 5020 = 5020
    expect(normalized[1].normalized).toBe(5020);
    // Next day: (2550 / 2500) * 5020 = 5120.4
    expect(normalized[2].normalized).toBe(5120.4);
    // Next day: (2525 / 2500) * 5020 = 5070.2
    expect(normalized[3].normalized).toBe(5070.2);
  });

  it('returns empty array when given empty input', () => {
    expect(normalizeSpSl20([])).toEqual([]);
  });

  it('calculates annualized rolling volatility with sqrt(252) scaling', () => {
    // Generate 25 points with known return values
    const points: MarketDataPoint[] = Array.from({ length: 25 }, (_, i) => ({
      date: `2024-01-${String(i + 1).padStart(2, '0')}`,
      aspi: 10000 + i * 10,
      sp_sl20: 3000 + i * 5,
      return: i % 2 === 0 ? 0.01 : -0.01,
      turnover: 1000000,
      volume: 50000,
    }));

    const vol = calculateRollingVolatility(points, 20);
    expect(vol).toHaveLength(25);
    // First 19 days should be null (warm-up)
    expect(vol[0].volatility).toBeNull();
    expect(vol[18].volatility).toBeNull();
    // Day 20 should have positive annualized volatility
    expect(vol[19].volatility).toBeGreaterThan(0);
    // ~1% std * sqrt(252) * 100% is approx 16% annualized
    expect(vol[19].volatility).toBeCloseTo(16.27, 0);
  });

  it('filters series by range presets correctly', () => {
    const dates = ['2024-01-01', '2024-06-01', '2024-11-01', '2024-12-01', '2024-12-15'];
    const points: MarketDataPoint[] = dates.map((d) => ({
      date: d,
      aspi: 11000,
      turnover: 1000000,
      volume: 50000,
    }));

    // All preset returns all points
    expect(filterPointsByPreset(points, 'All')).toHaveLength(5);

    // 1M preset returns points in last month
    const oneMonth = filterPointsByPreset(points, '1M');
    expect(oneMonth.length).toBeGreaterThanOrEqual(1);
    expect(oneMonth.every((p) => p.date >= '2024-11-15')).toBe(true);

    // 6M preset returns points in last 6 months
    const sixMonths = filterPointsByPreset(points, '6M');
    expect(sixMonths.length).toBeGreaterThanOrEqual(3);
  });
});
