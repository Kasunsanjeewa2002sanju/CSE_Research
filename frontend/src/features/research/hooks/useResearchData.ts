import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  researchIndexResponseSchema,
  researchAuditReportResponseSchema,
  researchExportsResponseSchema,
} from '@/api/zod-schemas';
import type {
  ResearchIndexResponse,
  ResearchAuditReportResponse,
  ResearchExportsResponse,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export function useResearchIndexQuery() {
  return useQuery<ResearchIndexResponse>({
    queryKey: queryKeys.research.index(),
    queryFn: () => apiFetch('/research/index', researchIndexResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useResearchAuditReportQuery() {
  return useQuery<ResearchAuditReportResponse>({
    queryKey: queryKeys.research.auditReport(),
    queryFn: () => apiFetch('/research/audit-report', researchAuditReportResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useResearchExportsQuery() {
  return useQuery<ResearchExportsResponse>({
    queryKey: queryKeys.research.exports(),
    queryFn: () => apiFetch('/research/exports', researchExportsResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}
