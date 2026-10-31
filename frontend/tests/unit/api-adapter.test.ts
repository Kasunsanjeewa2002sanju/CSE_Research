import { describe, it, expect } from 'vitest';
import { overviewSummarySchema } from '@/features/overview/api';
import { testOverviewPayload, testInvalidPayload } from '../fixtures/mock-data';

describe('API Boundary Validation Adapter (Rule FR4)', () => {
  it('successfully parses valid API response matching schema', () => {
    const result = overviewSummarySchema.safeParse(testOverviewPayload);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.aspi_current).toBe(11450.25);
      expect(result.data.sample_size_events).toBe(24);
    }
  });

  it('rejects invalid payload and exposes Zod contract errors', () => {
    const result = overviewSummarySchema.safeParse(testInvalidPayload);
    expect(result.success).toBe(false);
    if (!result.success) {
      const issuePaths = result.error.issues.map((i) => i.path.join('.'));
      expect(issuePaths).toContain('aspi_current');
    }
  });
});
