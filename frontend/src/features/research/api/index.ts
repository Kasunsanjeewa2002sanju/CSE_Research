import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { ResearchAuditResponse } from '../types';

export const auditProofSchema = z.object({
  dimension: z.string(),
  verdict: z.enum(['PASS', 'FAIL']),
  details: z.string(),
  evidence: z.string(),
});

export const researchAuditResponseSchema = z.object({
  stage: z.string(),
  audit_date: z.string(),
  proofs: z.array(auditProofSchema),
  master_index_available: z.boolean(),
});

export async function fetchResearchAudit(): Promise<ResearchAuditResponse> {
  return apiFetch('/research/audit', researchAuditResponseSchema);
}
