import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  eventsListResponseSchema,
  eventDetailSchema,
  eventsCoverageSchema,
} from '@/api/zod-schemas';
import type { EventsListResponse, EventDetail, EventsCoverage } from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export interface EventFilterParams {
  category?: string;
  type?: string;
  stage?: string;
  yearFrom?: number;
  yearTo?: number;
  samplePeriod?: boolean;
  isOverlapping?: boolean;
  addedByResearcher?: boolean;
  limit?: number;
}

export function useEventsListQuery(params?: EventFilterParams | string) {
  const normalizedParams: EventFilterParams =
    typeof params === 'string' ? { category: params } : (params ?? {});

  const searchParams: Record<string, string | number | boolean> = {};
  if (normalizedParams.category && normalizedParams.category !== 'All') {
    searchParams.category = normalizedParams.category;
  }
  if (normalizedParams.stage && normalizedParams.stage !== 'All') {
    searchParams.stage = normalizedParams.stage;
  }
  if (normalizedParams.yearFrom) searchParams.yearFrom = normalizedParams.yearFrom;
  if (normalizedParams.yearTo) searchParams.yearTo = normalizedParams.yearTo;
  if (normalizedParams.samplePeriod !== undefined)
    searchParams.samplePeriod = normalizedParams.samplePeriod;
  if (normalizedParams.isOverlapping !== undefined)
    searchParams.isOverlapping = normalizedParams.isOverlapping;
  if (normalizedParams.addedByResearcher !== undefined)
    searchParams.addedByResearcher = normalizedParams.addedByResearcher;
  if (normalizedParams.limit) searchParams.limit = normalizedParams.limit;

  const keyString = JSON.stringify(searchParams);

  return useQuery<EventsListResponse>({
    queryKey: [...queryKeys.events.list(normalizedParams.category), keyString],
    queryFn: () =>
      apiFetch('/events', eventsListResponseSchema, {
        searchParams: Object.keys(searchParams).length > 0 ? searchParams : undefined,
      }),
    staleTime: getDynamicInterval('events'),
  });
}

export function useEventDetailQuery(eventId: string) {
  return useQuery<EventDetail>({
    queryKey: queryKeys.events.detail(eventId),
    queryFn: () => apiFetch(`/events/${eventId}`, eventDetailSchema),
    enabled: Boolean(eventId),
    staleTime: getDynamicInterval('events'),
  });
}

export function useEventsCoverageQuery() {
  return useQuery<EventsCoverage>({
    queryKey: queryKeys.events.coverage(),
    queryFn: () => apiFetch('/events/coverage', eventsCoverageSchema),
    staleTime: getDynamicInterval('events'),
  });
}
