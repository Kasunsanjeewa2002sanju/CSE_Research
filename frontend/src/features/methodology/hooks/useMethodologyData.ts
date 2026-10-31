import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { protocolResponseSchema, featureDictionaryResponseSchema } from '@/api/zod-schemas';
import type { ProtocolResponse, FeatureDictionaryResponse } from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export function useProtocolQuery() {
  return useQuery<ProtocolResponse>({
    queryKey: queryKeys.protocol.phases(),
    queryFn: () => apiFetch('/protocol', protocolResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}

export function useFeatureDictionaryQuery() {
  return useQuery<FeatureDictionaryResponse>({
    queryKey: queryKeys.protocol.dictionary(),
    queryFn: () => apiFetch('/features/dictionary', featureDictionaryResponseSchema),
    staleTime: getDynamicInterval('models'),
  });
}
