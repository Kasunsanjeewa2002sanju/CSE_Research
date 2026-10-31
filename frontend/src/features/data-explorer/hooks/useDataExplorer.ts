import { useQuery } from '@tanstack/react-query';
import { fetchAspiHistory } from '../api';
import type { AspiHistoryResponse } from '../types';

export function useAspiHistory() {
  return useQuery<AspiHistoryResponse>({
    queryKey: ['aspi', 'history'],
    queryFn: fetchAspiHistory,
  });
}
