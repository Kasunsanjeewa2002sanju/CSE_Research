import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  marketSummarySchema,
  marketSeriesResponseSchema,
  marketStatsSchema,
  marketIntradayResponseSchema,
} from '@/api/zod-schemas';
import type {
  MarketSummary,
  MarketSeriesResponse,
  MarketStats,
  MarketIntradayResponse,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

/**
 * Hook for fetching high-level market summary (ASPI, S&P SL 20, turnover, vol).
 * Cache intervals derived dynamically from API meta.
 */
export function useMarketSummaryQuery() {
  return useQuery<MarketSummary>({
    queryKey: queryKeys.market.summary(),
    queryFn: () => apiFetch('/market/summary', marketSummarySchema),
    refetchInterval: getDynamicInterval('market'),
    staleTime: getDynamicInterval('market') / 2,
  });
}

/**
 * Hook for historical ASPI series and trading volume.
 */
export function useMarketSeriesQuery(range = '1Y') {
  return useQuery<MarketSeriesResponse>({
    queryKey: queryKeys.market.series(range),
    queryFn: () =>
      apiFetch('/market/series', marketSeriesResponseSchema, {
        searchParams: { range },
      }),
    refetchInterval: getDynamicInterval('market') * 2,
    staleTime: getDynamicInterval('market'),
  });
}

/**
 * Hook for fetching derived econometric and market statistics (/market/stats).
 * Provides panel_size_days, realized_volatility_annualized, baseline_aspi, as_of_date.
 */
export function useMarketStatsQuery() {
  return useQuery<MarketStats>({
    queryKey: queryKeys.market.stats(),
    queryFn: () => apiFetch('/market/stats', marketStatsSchema),
    refetchInterval: getDynamicInterval('market'),
    staleTime: 15 * 1000,
  });
}

/**
 * Hook for fetching rolling 1-minute intraday downsampled series for sparklines (/market/intraday).
 */
export function useMarketIntradayQuery(metric = 'aspi', session = 'current') {
  return useQuery<MarketIntradayResponse>({
    queryKey: queryKeys.market.intraday(metric),
    queryFn: () =>
      apiFetch('/market/intraday', marketIntradayResponseSchema, {
        searchParams: { metric, session },
      }),
    refetchInterval: 15 * 1000,
    staleTime: 10 * 1000,
  });
}
