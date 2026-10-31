import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  newsItemsResponseSchema,
  newsItemDetailResponseSchema,
  newsFeedsResponseSchema,
  pipelineRunsResponseSchema,
  pipelineStatsResponseSchema,
} from '@/api/zod-schemas';
import type {
  NewsItemsResponse,
  NewsItemDetailResponse,
  NewsFeedsResponse,
  PipelineRunsResponse,
  PipelineStatsResponse,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export interface UseNewsItemsParams {
  page?: number;
  pageSize?: number;
  source?: string;
  category?: string;
  stage?: string;
  relevance?: string;
  language?: string;
  evidenceStrength?: string;
  search?: string;
  fromDate?: string;
  toDate?: string;
}

export function useNewsItemsQuery(
  paramsOrPage: UseNewsItemsParams | number = 1,
  pageSizeArg?: number
) {
  const params: UseNewsItemsParams =
    typeof paramsOrPage === 'number'
      ? { page: paramsOrPage, pageSize: pageSizeArg ?? 24 }
      : paramsOrPage;

  const {
    page = 1,
    pageSize = 24,
    source,
    category,
    stage,
    relevance,
    language,
    evidenceStrength,
    search,
    fromDate,
    toDate,
  } = params;

  const searchParams: Record<string, string | number> = {
    page,
    page_size: pageSize,
  };

  if (source && source !== 'all') searchParams.source = source;
  if (category && category !== 'all') searchParams.category = category;
  if (stage && stage !== 'all') searchParams.stage = stage;
  if (relevance && relevance !== 'all') searchParams.relevance = relevance;
  if (language && language !== 'all') searchParams.language = language;
  if (evidenceStrength && evidenceStrength !== 'all') searchParams.evidence_strength = evidenceStrength;
  if (search && search.trim()) searchParams.search = search.trim();
  if (fromDate) searchParams.from = fromDate;
  if (toDate) searchParams.to = toDate;

  return useQuery<NewsItemsResponse>({
    queryKey: queryKeys.news.items(searchParams),
    queryFn: () =>
      apiFetch('/news/items', newsItemsResponseSchema, {
        searchParams,
      }),
    refetchInterval: getDynamicInterval('news'),
    staleTime: getDynamicInterval('news') / 2,
  });
}

export function useNewsItemDetailQuery(itemId: string | null) {
  return useQuery<NewsItemDetailResponse>({
    queryKey: queryKeys.news.itemDetail(itemId || ''),
    queryFn: () => apiFetch(`/news/items/${itemId}`, newsItemDetailResponseSchema),
    enabled: Boolean(itemId),
    staleTime: getDynamicInterval('news'),
  });
}

export function useNewsFeedsQuery() {
  return useQuery<NewsFeedsResponse>({
    queryKey: queryKeys.news.feeds(),
    queryFn: () => apiFetch('/news/feeds', newsFeedsResponseSchema),
    refetchInterval: getDynamicInterval('news'),
    staleTime: getDynamicInterval('news'),
  });
}

export function usePipelineStatsQuery() {
  return useQuery<PipelineStatsResponse>({
    queryKey: queryKeys.news.pipelineStats(),
    queryFn: () => apiFetch('/news/pipeline-stats', pipelineStatsResponseSchema),
    refetchInterval: getDynamicInterval('news'),
    staleTime: getDynamicInterval('news'),
  });
}

export function usePipelineRunsQuery() {
  return useQuery<PipelineRunsResponse>({
    queryKey: queryKeys.news.pipelineRuns(),
    queryFn: () => apiFetch('/news/pipeline-runs', pipelineRunsResponseSchema),
    refetchInterval: getDynamicInterval('news'),
    staleTime: getDynamicInterval('news'),
  });
}
