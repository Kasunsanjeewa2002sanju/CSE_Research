import { useQuery } from '@tanstack/react-query';
import { fetchResearchAudit } from '../api';
import type { ResearchAuditResponse } from '../types';

export function useResearchAudit() {
  return useQuery<ResearchAuditResponse>({
    queryKey: ['research', 'audit'],
    queryFn: fetchResearchAudit,
  });
}
