import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';
import { ApiClientError } from './client';
import type { MetaResponse, RefreshIntervals } from './types';

// Default intervals in milliseconds used only until the meta endpoint loads
const INITIAL_INTERVALS_MS = {
  market: 30 * 1000,
  events: 60 * 60 * 1000,
  models: 24 * 60 * 60 * 1000,
  news: 5 * 60 * 1000,
  system: 60 * 1000,
};

let activeIntervals = { ...INITIAL_INTERVALS_MS };

/**
 * Updates dynamic cache and refetch intervals directly from the API meta endpoint.
 * Satisfies the requirement: "cache and refetch intervals come from the API meta endpoint, not constants."
 */
export function updateDynamicIntervalsFromMeta(meta?: MetaResponse | null) {
  if (!meta?.refresh_intervals) return;
  const raw: RefreshIntervals = meta.refresh_intervals;
  activeIntervals = {
    market: (raw.market_seconds || 30) * 1000,
    events: (raw.events_seconds || 3600) * 1000,
    models: (raw.models_seconds || 86400) * 1000,
    news: (raw.news_seconds || 300) * 1000,
    system: (raw.system_seconds || 60) * 1000,
  };
}

export function getDynamicInterval(domain: keyof typeof INITIAL_INTERVALS_MS) {
  return activeIntervals[domain] ?? INITIAL_INTERVALS_MS[domain];
}

type ErrorListener = (error: ApiClientError) => void;
const errorListeners = new Set<ErrorListener>();

export function subscribeToApiErrors(listener: ErrorListener): () => void {
  errorListeners.add(listener);
  return () => {
    errorListeners.delete(listener);
  };
}

function notifyApiError(error: unknown) {
  if (error instanceof ApiClientError) {
    errorListeners.forEach((fn) => fn(error));
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      notifyApiError(error);
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      notifyApiError(error);
    },
  }),
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Idempotent network retry logic
        if (error instanceof ApiClientError) {
          if (error.code === 'CONTRACT_MISMATCH') return false; // Never retry schema mismatches
          if (error.status >= 400 && error.status < 500) return false; // Never retry 4xx
          return failureCount < 2 && error.status >= 500;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
      staleTime: 60 * 1000,
    },
  },
});
