import { useQuery } from '@tanstack/react-query';
import { fetchNewsArticles } from '../api';
import type { NewsResponse } from '../types';

export function useNews() {
  return useQuery<NewsResponse>({
    queryKey: ['news', 'articles'],
    queryFn: fetchNewsArticles,
  });
}
