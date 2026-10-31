/**
 * Pure calculation utilities for Data Explorer charts and series
 */

export interface MarketDataPoint {
  date: string;
  aspi: number;
  sp_sl20?: number | null;
  return?: number | null;
  turnover: number;
  volume: number;
}

/**
 * Normalizes S&P SL 20 to the ASPI level at the first date S&P SL 20 is valid.
 * Base formula: (SP_t / SP_0) * ASPI_0
 */
export function normalizeSpSl20(
  points: MarketDataPoint[]
): Array<{ date: string; normalized: number | null }> {
  if (!points || points.length === 0) return [];

  // Find first point where S&P SL 20 exists and is positive
  const basePoint = points.find(
    (p) => p.sp_sl20 !== undefined && p.sp_sl20 !== null && p.sp_sl20 > 0
  );
  if (!basePoint || !basePoint.sp_sl20) {
    return points.map((p) => ({ date: p.date, normalized: null }));
  }

  const baseSp = basePoint.sp_sl20;
  const baseAspi = basePoint.aspi;

  return points.map((p) => {
    if (p.sp_sl20 === undefined || p.sp_sl20 === null || p.sp_sl20 <= 0) {
      return { date: p.date, normalized: null };
    }
    const norm = (p.sp_sl20 / baseSp) * baseAspi;
    return { date: p.date, normalized: Number(norm.toFixed(2)) };
  });
}

/**
 * Calculates annualized rolling volatility from returns over a given trading day window.
 * Formula: std(r_{t-W:t}) * sqrt(252) * 100%
 */
export function calculateRollingVolatility(
  points: MarketDataPoint[],
  windowDays = 20
): Array<{ date: string; volatility: number | null }> {
  if (!points || points.length < windowDays) return [];

  const returns = points.map((p) => p.return ?? 0);
  const sqrt252 = Math.sqrt(252);

  return points.map((p, idx) => {
    if (idx < windowDays - 1) {
      return { date: p.date, volatility: null };
    }

    const windowReturns = returns.slice(idx - windowDays + 1, idx + 1);
    const mean = windowReturns.reduce((a, b) => a + b, 0) / windowDays;
    const variance =
      windowReturns.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (windowDays - 1);
    const std = Math.sqrt(variance);
    const annVol = std * sqrt252 * 100;

    return { date: p.date, volatility: Number(annVol.toFixed(2)) };
  });
}

/**
 * Filter points by predefined preset relative to the latest available date
 */
export type RangePreset = '1M' | '3M' | '6M' | '1Y' | '5Y' | 'All';

export function filterPointsByPreset(
  points: MarketDataPoint[],
  preset: RangePreset
): MarketDataPoint[] {
  if (!points || points.length === 0 || preset === 'All') {
    return points;
  }

  const lastDate = new Date(points[points.length - 1].date);
  const cutoff = new Date(lastDate);

  switch (preset) {
    case '1M':
      cutoff.setMonth(cutoff.getMonth() - 1);
      break;
    case '3M':
      cutoff.setMonth(cutoff.getMonth() - 3);
      break;
    case '6M':
      cutoff.setMonth(cutoff.getMonth() - 6);
      break;
    case '1Y':
      cutoff.setFullYear(cutoff.getFullYear() - 1);
      break;
    case '5Y':
      cutoff.setFullYear(cutoff.getFullYear() - 5);
      break;
  }

  const cutoffStr = cutoff.toISOString().substring(0, 10);
  return points.filter((p) => p.date >= cutoffStr);
}
