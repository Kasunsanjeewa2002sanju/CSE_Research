import { apiFetch } from '@/api/client';
import { modelLeaderboardResponseSchema } from '@/api/zod-schemas';
import type { ModelLeaderboardResponse } from '../types';

export { modelLeaderboardItemSchema, modelLeaderboardResponseSchema } from '@/api/zod-schemas';

export async function fetchModelLeaderboard(): Promise<ModelLeaderboardResponse> {
  return apiFetch('/models/leaderboard', modelLeaderboardResponseSchema);
}
