import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  eventStudyCaarResponseSchema,
  eventStudySubgroupsResponseSchema,
  eventStudyHeatmapResponseSchema,
  eventStudyPerEventResponseSchema,
  eventStudySummaryResponseSchema,
} from '@/api/zod-schemas';
import type {
  EventStudyCaarResponse,
  EventStudySubgroupsResponse,
  EventStudyHeatmapResponse,
  EventStudyPerEventResponse,
  EventStudySummaryResponse,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export interface UseCaarQueryParams {
  window?: string;
  election_type?: string;
  stage?: string;
  model_type?: string;
  estimation_len?: number;
  include_overlapping?: boolean;
}

export function useEventStudyCaarQuery(params?: UseCaarQueryParams) {
  const windowStr = params?.window ?? '[-7,+7]';
  const electionType = params?.election_type ?? 'All';
  const stage = params?.stage ?? 'polling';
  const modelType = params?.model_type ?? 'mean_adjusted';
  const estLen = params?.estimation_len ?? 15;
  const includeOverlap = params?.include_overlapping ?? true;

  return useQuery<EventStudyCaarResponse>({
    queryKey: queryKeys.eventStudy.caar({
      window: windowStr,
      electionType,
      stage,
      modelType,
      estLen,
      includeOverlap,
    }),
    queryFn: () =>
      apiFetch('/event-study/caar', eventStudyCaarResponseSchema, {
        searchParams: {
          window: windowStr,
          election_type: electionType,
          stage,
          model_type: modelType,
          estimation_len: estLen,
          include_overlapping: includeOverlap,
        },
      }),
    staleTime: getDynamicInterval('events'),
  });
}

export function useEventStudyHeatmapQuery() {
  return useQuery<EventStudyHeatmapResponse>({
    queryKey: queryKeys.eventStudy.heatmap(),
    queryFn: () => apiFetch('/event-study/heatmap', eventStudyHeatmapResponseSchema),
    staleTime: getDynamicInterval('events'),
  });
}

export interface UsePerEventQueryParams {
  window?: string;
  election_type?: string;
  stage?: string;
  include_overlapping?: boolean;
}

export function useEventStudyPerEventQuery(params?: UsePerEventQueryParams) {
  const windowStr = params?.window ?? '[0,+7]';
  const electionType = params?.election_type;
  const stage = params?.stage;
  const includeOverlap = params?.include_overlapping ?? true;

  const searchParams: Record<string, string | number | boolean> = {
    window: windowStr,
    include_overlapping: includeOverlap,
  };
  if (electionType && electionType !== 'All') {
    searchParams.election_type = electionType;
  }
  if (stage && stage !== 'All') {
    searchParams.stage = stage;
  }

  return useQuery<EventStudyPerEventResponse>({
    queryKey: queryKeys.eventStudy.perEvent({
      window: windowStr,
      electionType,
      stage,
      includeOverlap,
    }),
    queryFn: () =>
      apiFetch('/event-study/per-event', eventStudyPerEventResponseSchema, {
        searchParams,
      }),
    staleTime: getDynamicInterval('events'),
  });
}

export function useEventStudySummaryQuery() {
  return useQuery<EventStudySummaryResponse>({
    queryKey: queryKeys.eventStudy.summary(),
    queryFn: () => apiFetch('/event-study/summary', eventStudySummaryResponseSchema),
    staleTime: getDynamicInterval('events'),
  });
}

export function useEventStudySubgroupsQuery(window = '[-20, +20]') {
  return useQuery<EventStudySubgroupsResponse>({
    queryKey: queryKeys.eventStudy.subgroups(window),
    queryFn: () =>
      apiFetch('/event-study/subgroups', eventStudySubgroupsResponseSchema, {
        searchParams: { window },
      }),
    staleTime: getDynamicInterval('events'),
  });
}
