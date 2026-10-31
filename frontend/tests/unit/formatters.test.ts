import { describe, it, expect } from 'vitest';
import {
  formatNumber,
  formatPercent,
  formatLKR,
  formatVolume,
  formatDate,
  formatDateColombo,
  formatDateTimeColombo,
  formatSampleSize,
  formatPValue,
  formatConfidenceInterval,
} from '@/utils/formatters';

describe('Stage 5: Data Formatters', () => {
  describe('formatNumber', () => {
    it('formats numbers with fixed decimals and thousands separators', () => {
      expect(formatNumber(1234.5678, 2)).toBe('1,234.57');
      expect(formatNumber(22865.0, 2)).toBe('22,865.00');
      expect(formatNumber(0, 2)).toBe('0.00');
    });

    it('returns em-dash for null, undefined, or NaN', () => {
      expect(formatNumber(null)).toBe('—');
      expect(formatNumber(undefined)).toBe('—');
      expect(formatNumber(NaN)).toBe('—');
    });
  });

  describe('formatPercent', () => {
    it('formats decimal ratios by multiplying by 100', () => {
      expect(formatPercent(0.0548, 2)).toBe('5.48%');
      expect(formatPercent(0.007917, 4, true)).toBe('+0.7917%');
      expect(formatPercent(-0.003418, 4, true)).toBe('-0.3418%');
    });

    it('formats raw percentages without multiplying when isRawPercent=true', () => {
      expect(formatPercent(13.0908, 4, true, true)).toBe('+13.0908%');
      expect(formatPercent(-0.34, 2, true, true)).toBe('-0.34%');
      expect(formatPercent(4.28, 2, false, true)).toBe('4.28%');
    });

    it('returns em-dash for null/undefined/NaN', () => {
      expect(formatPercent(null)).toBe('—');
      expect(formatPercent(undefined)).toBe('—');
      expect(formatPercent(NaN)).toBe('—');
    });
  });

  describe('formatLKR', () => {
    it('formats billions with B suffix', () => {
      expect(formatLKR(9309760000.0, 2)).toBe('LKR 9.31B');
      expect(formatLKR(2840000000.0, 2)).toBe('LKR 2.84B');
    });

    it('formats millions with M suffix', () => {
      expect(formatLKR(45000000.0, 2)).toBe('LKR 45.00M');
    });

    it('formats thousands with K suffix', () => {
      expect(formatLKR(500000.0, 2)).toBe('LKR 500.00K');
    });

    it('formats small amounts', () => {
      expect(formatLKR(250.5, 2)).toBe('LKR 250.50');
      expect(formatLKR(0, 2)).toBe('LKR 0.00');
    });

    it('returns em-dash for null/undefined/NaN', () => {
      expect(formatLKR(null)).toBe('—');
      expect(formatLKR(undefined)).toBe('—');
      expect(formatLKR(NaN)).toBe('—');
    });
  });

  describe('formatVolume', () => {
    it('formats millions with M suffix', () => {
      expect(formatVolume(245620000, 1)).toBe('245.6M');
      expect(formatVolume(85400000, 1)).toBe('85.4M');
    });

    it('formats thousands with K suffix', () => {
      expect(formatVolume(750000, 1)).toBe('750.0K');
    });

    it('formats small unit counts', () => {
      expect(formatVolume(500, 1)).toBe('500');
      expect(formatVolume(0, 1)).toBe('0');
    });

    it('returns em-dash for null/undefined/NaN', () => {
      expect(formatVolume(null)).toBe('—');
      expect(formatVolume(undefined)).toBe('—');
      expect(formatVolume(NaN)).toBe('—');
    });
  });

  describe('formatDateColombo & formatDateTimeColombo', () => {
    it('formats date in standard format', () => {
      expect(formatDate('2026-10-20T10:31:28+00:00')).toBe('Oct 20, 2026');
      expect(formatDate(null)).toBe('—');
    });

    it('formats date in Asia/Colombo timezone', () => {
      const formatted = formatDateColombo('2026-10-20T10:31:28+00:00');
      expect(formatted).toBe('20 Oct 2026');
    });

    it('formats datetime with timezone suffix', () => {
      const formatted = formatDateTimeColombo('2026-10-20T10:31:28+00:00', true, true);
      expect(formatted).toContain('Asia/Colombo');
      expect(formatted).toContain('2026');
    });

    it('returns em-dash for null/undefined', () => {
      expect(formatDateColombo(null)).toBe('—');
      expect(formatDateTimeColombo(null)).toBe('—');
    });
  });

  describe('Statistical Formatters', () => {
    it('formats sample sizes (n) per Rule FR5', () => {
      expect(formatSampleSize(24)).toBe('n = 24');
      expect(formatSampleSize(null)).toBe('n = —');
    });

    it('formats p-values with statistical significance threshold', () => {
      expect(formatPValue(0.018)).toBe('p = 0.018');
      expect(formatPValue(0.00001)).toBe('p < 0.001');
      expect(formatPValue(null)).toBe('p = —');
    });

    it('formats confidence intervals', () => {
      expect(formatConfidenceInterval(-0.01, 0.05)).toBe('[-1.00%, +5.00%]');
      expect(formatConfidenceInterval(null, null)).toBe('[—, —]');
    });
  });
});
