import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { AspiHistoryResponse } from '../types';

export const aspiDataPointSchema = z.object({
  date: z.string(),
  close: z.number(),
  log_return: z.number(),
  volume: z.number().optional(),
  turnover: z.number().optional(),
});

export const aspiHistoryResponseSchema = z.object({
  series: z.array(aspiDataPointSchema),
  total_records: z.number(),
  start_date: z.string(),
  end_date: z.string(),
});

export async function fetchAspiHistory(): Promise<AspiHistoryResponse> {
  return apiFetch('/aspi/history', aspiHistoryResponseSchema);
}
