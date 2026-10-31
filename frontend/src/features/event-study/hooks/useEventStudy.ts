import { useQuery } from '@tanstack/react-query';
import { fetchEventStudyCaar } from '../api';
import type { EventStudyCaarResponse } from '../types';

export function useEventStudy() {
  return useQuery<EventStudyCaarResponse>({
    queryKey: ['event-study', 'caar'],
    queryFn: fetchEventStudyCaar,
  });
}
