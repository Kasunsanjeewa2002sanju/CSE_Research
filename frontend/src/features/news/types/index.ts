import type { NewsItem } from '@/api/types';

export type {
  NewsItem,
  NewsItemsResponse,
  NewsItemDetailResponse,
  NewsFeedItem,
  NewsFeedsResponse,
  PipelineRunItem,
  PipelineRunsResponse,
  DuplicateClusterItem,
  NewsFilters,
  FailureLogItem,
  ItemsPerHourItem,
  ClassificationDistributionItem,
  LanguageSplitItem,
  RelevanceFunnelStage,
  RelevanceFunnel,
  PipelineStatsSummary,
  PipelineStatsResponse,
} from '@/api/types';

export type NewsArticle = NewsItem;

export interface NewsResponse {
  articles: NewsItem[];
  active_feeds_count: number;
  last_polled_at: string;
}

export interface NewsFilterState {
  source: string;
  category: string;
  stage: string;
  relevance: string;
  language: string;
  evidenceStrength: string;
  search: string;
  fromDate: string;
  toDate: string;
}
