import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { marketSeriesResponseSchema, dataAuditSchema } from '@/api/zod-schemas';
import type { MarketSeriesResponse, DataAudit } from '@/api/types';
import { getDynamicInterval } from '@/api/query-client';

export function useDataExplorerSeriesQuery(range = 'All') {
  return useQuery<MarketSeriesResponse>({
    queryKey: queryKeys.market.series(range),
    queryFn: () =>
      apiFetch('/market/series', marketSeriesResponseSchema, {
        searchParams: { range },
      }),
    staleTime: getDynamicInterval('market'),
  });
}

export function useDataAuditQuery() {
  return useQuery<DataAudit>({
    queryKey: queryKeys.dataAudit.summary(),
    queryFn: () => apiFetch('/data/audit', dataAuditSchema),
    staleTime: getDynamicInterval('events'),
  });
}

export const useMarketSeriesQuery = useDataExplorerSeriesQuery;
