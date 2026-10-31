import { useQuery } from '@tanstack/react-query';
import { fetchOverviewSummary } from '../api';
import type { OverviewSummary } from '../types';

export function useOverviewSummary() {
  return useQuery<OverviewSummary>({
    queryKey: ['overview', 'summary'],
    queryFn: fetchOverviewSummary,
  });
}
