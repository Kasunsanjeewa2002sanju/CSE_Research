import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { ScenarioParams, ScenarioResult } from '../types';

export const scenarioResultSchema = z.object({
  predicted_return: z.number(),
  conformal_80_lower: z.number(),
  conformal_80_upper: z.number(),
  conformal_95_lower: z.number(),
  conformal_95_upper: z.number(),
  model_used: z.string(),
});

export async function evaluateScenario(params: ScenarioParams): Promise<ScenarioResult> {
  return apiFetch('/scenarios/evaluate', scenarioResultSchema, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
