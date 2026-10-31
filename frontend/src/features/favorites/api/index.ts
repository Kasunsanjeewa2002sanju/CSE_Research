import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { FavoritesResponse } from '../types';

export const favoriteItemSchema = z.object({
  id: z.string(),
  item_type: z.enum(['event', 'model', 'chart']),
  title: z.string(),
  saved_at: z.string(),
  path: z.string(),
});

export const favoritesResponseSchema = z.object({
  favorites: z.array(favoriteItemSchema),
});

export async function fetchFavorites(): Promise<FavoritesResponse> {
  return apiFetch('/user/favorites', favoritesResponseSchema);
}
