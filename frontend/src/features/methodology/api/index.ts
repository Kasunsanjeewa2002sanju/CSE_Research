import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { MethodologyResponse } from '../types';

export const protocolRuleSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  description: z.string(),
  enforcement: z.string(),
});

export const methodologyResponseSchema = z.object({
  phases_count: z.number(),
  protocol_rules: z.array(protocolRuleSchema),
  leakage_audit_status: z.string(),
});

export async function fetchMethodology(): Promise<MethodologyResponse> {
  return apiFetch('/methodology', methodologyResponseSchema);
}
