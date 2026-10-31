import { useQuery } from '@tanstack/react-query';
import { fetchMethodology } from '../api';
import type { MethodologyResponse } from '../types';

export function useMethodology() {
  return useQuery<MethodologyResponse>({
    queryKey: ['methodology', 'protocol'],
    queryFn: fetchMethodology,
  });
}
