import { useQuery } from '@tanstack/react-query';
import { fetchModelLeaderboard } from '../api';
import type { ModelLeaderboardResponse } from '../types';

export function useModelLeaderboard() {
  return useQuery<ModelLeaderboardResponse>({
    queryKey: ['models', 'leaderboard'],
    queryFn: fetchModelLeaderboard,
  });
}
