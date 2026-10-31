import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { favoritesResponseSchema, susSurveyResponseSchema } from '@/api/zod-schemas';
import type { FavoritesResponse, SusSurveyResponse } from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export function useFavoritesQuery() {
  return useQuery<FavoritesResponse>({
    queryKey: queryKeys.user.favorites(),
    queryFn: () => apiFetch('/user/favorites', favoritesResponseSchema),
    staleTime: getDynamicInterval('system'),
  });
}

export function useSusSurveyQuery() {
  return useQuery<SusSurveyResponse>({
    queryKey: queryKeys.user.sus(),
    queryFn: () => apiFetch('/survey/sus', susSurveyResponseSchema),
    staleTime: getDynamicInterval('system') * 10,
  });
}
