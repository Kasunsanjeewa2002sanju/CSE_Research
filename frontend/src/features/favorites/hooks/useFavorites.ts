import { useQuery } from '@tanstack/react-query';
import { fetchFavorites } from '../api';
import type { FavoritesResponse } from '../types';

export function useFavorites() {
  return useQuery<FavoritesResponse>({
    queryKey: ['user', 'favorites'],
    queryFn: fetchFavorites,
  });
}
