import { useMutation, useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  scenarioSubmitResponseSchema,
  scenarioEvidenceSchema,
  scenarioBacktestsResponseSchema,
} from '@/api/zod-schemas';
import type {
  ScenarioSubmitRequest,
  ScenarioSubmitResponse,
  ScenarioEvidence,
  ScenarioBacktestsResponse,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export function useScenarioSubmitMutation() {
  return useMutation<ScenarioSubmitResponse, Error, ScenarioSubmitRequest>({
    mutationFn: (requestPayload) =>
      apiFetch('/scenario', scenarioSubmitResponseSchema, {
        method: 'POST',
        body: requestPayload,
      }),
  });
}

// Backward compatibility mutation for old callers
export function useScenarioPredictMutation() {
  return useMutation<ScenarioSubmitResponse, Error, ScenarioSubmitRequest>({
    mutationFn: (requestPayload) =>
      apiFetch('/scenario', scenarioSubmitResponseSchema, {
        method: 'POST',
        body: requestPayload,
      }),
  });
}

export function useScenarioEvidenceQuery(category?: string, stage?: string) {
  const queryParams = new URLSearchParams();
  if (category) queryParams.set('category', category);
  if (stage) queryParams.set('stage', stage);
  const qStr = queryParams.toString() ? `?${queryParams.toString()}` : '';

  return useQuery<ScenarioEvidence>({
    queryKey: queryKeys.scenarios.evidence({ category, stage }),
    queryFn: () => apiFetch(`/scenario/evidence${qStr}`, scenarioEvidenceSchema),
    staleTime: getDynamicInterval('models'),
    enabled: Boolean(category),
  });
}

export function useScenarioBacktestsQuery() {
  return useQuery<ScenarioBacktestsResponse>({
    queryKey: queryKeys.scenarios.backtests(),
    queryFn: () => apiFetch('/scenario/back-tests', scenarioBacktestsResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}
