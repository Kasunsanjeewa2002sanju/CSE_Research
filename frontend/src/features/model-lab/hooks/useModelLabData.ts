import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import {
  modelLeaderboardResponseSchema,
  modelDetailResponseSchema,
  modelCompareResponseSchema,
  modelStatisticsResponseSchema,
  finalModelResponseSchema,
  modelArtifactSchema,
} from '@/api/zod-schemas';
import type {
  ModelLeaderboardResponse,
  ModelDetailResponse,
  ModelCompareResponse,
  ModelStatisticsResponse,
  FinalModelResponse,
  ModelArtifact,
} from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';
import { z } from 'zod';

export function useModelLeaderboardQuery() {
  return useQuery<ModelLeaderboardResponse>({
    queryKey: queryKeys.models.leaderboard(),
    queryFn: () => apiFetch('/models/leaderboard', modelLeaderboardResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useModelDetailQuery(modelId = 'catboost_reg_c_h5') {
  return useQuery<ModelDetailResponse>({
    queryKey: queryKeys.models.detail(modelId),
    queryFn: () =>
      apiFetch('/models/detail', modelDetailResponseSchema, {
        searchParams: { model_id: modelId },
      }),
    staleTime: getDynamicInterval('models'),
  });
}

export function useModelCompareQuery(modelIds?: string) {
  const ids = modelIds || 'catboost_reg_c_h5,xgboost_reg_c_h5,timesfm_log_returns_ctx64_h5,historical_mean';
  return useQuery<ModelCompareResponse>({
    queryKey: queryKeys.models.compare(ids),
    queryFn: () =>
      apiFetch('/models/compare', modelCompareResponseSchema, {
        searchParams: { model_ids: ids },
      }),
    staleTime: getDynamicInterval('models'),
  });
}

export function useModelStatisticsQuery() {
  return useQuery<ModelStatisticsResponse>({
    queryKey: queryKeys.models.statistics(),
    queryFn: () => apiFetch('/models/statistics', modelStatisticsResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useFinalModelQuery() {
  return useQuery<FinalModelResponse>({
    queryKey: queryKeys.models.final(),
    queryFn: () => apiFetch('/models/final', finalModelResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useModelArtifactsQuery() {
  return useQuery<{ artifacts: ModelArtifact[] }>({
    queryKey: queryKeys.models.artifacts(),
    queryFn: () =>
      apiFetch(
        '/models/artifacts',
        z.object({ artifacts: z.array(modelArtifactSchema) })
      ),
    staleTime: getDynamicInterval('models'),
  });
}
