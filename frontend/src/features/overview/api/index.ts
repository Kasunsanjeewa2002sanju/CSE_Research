import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { OverviewSummary } from '../types';

export const overviewSummarySchema = z.object({
  aspi_current: z.number(),
  daily_return: z.number(),
  sample_size_events: z.number(),
  champion_model_name: z.string(),
  champion_oos_r2: z.number(),
  champion_directional_accuracy: z.number(),
  data_as_of: z.string(),
  is_stale: z.boolean(),
  disclaimer: z.string(),
});

export async function fetchOverviewSummary(): Promise<OverviewSummary> {
  return apiFetch('/overview/summary', overviewSummarySchema);
}
