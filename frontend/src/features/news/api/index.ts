import { apiFetch } from '@/api/client';
import {
  newsItemsResponseSchema,
  newsItemDetailResponseSchema,
  newsFeedsResponseSchema,
  pipelineStatsResponseSchema,
  pipelineRunsResponseSchema,
} from '@/api/zod-schemas';
import type {
  NewsItemsResponse,
  NewsItemDetailResponse,
  NewsFeedsResponse,
  PipelineStatsResponse,
  PipelineRunsResponse,
  NewsResponse,
} from '../types';

export async function fetchNewsItems(
  params: Record<string, string | number | undefined> = {}
): Promise<NewsItemsResponse> {
  const searchParams: Record<string, string | number> = {};
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== '' && val !== 'all') {
      searchParams[key] = val;
    }
  }
  return apiFetch('/news/items', newsItemsResponseSchema, { searchParams });
}

export async function fetchNewsArticles(): Promise<NewsResponse> {
  const data = await fetchNewsItems({ pageSize: 20 });
  return {
    articles: data.items,
    active_feeds_count: 8,
    last_polled_at: data.items[0]?.published_at || new Date().toISOString(),
  };
}

export async function fetchNewsItem(id: string): Promise<NewsItemDetailResponse> {
  return apiFetch(`/news/items/${id}`, newsItemDetailResponseSchema);
}

export async function fetchNewsFeeds(): Promise<NewsFeedsResponse> {
  return apiFetch('/news/feeds', newsFeedsResponseSchema);
}

export async function fetchPipelineStats(): Promise<PipelineStatsResponse> {
  return apiFetch('/news/pipeline-stats', pipelineStatsResponseSchema);
}

export async function fetchPipelineRuns(): Promise<PipelineRunsResponse> {
  return apiFetch('/news/pipeline-runs', pipelineRunsResponseSchema);
}
