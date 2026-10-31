import React, { createContext, useContext, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { metaResponseSchema, systemStatusSchema } from '@/api/zod-schemas';
import type { MetaResponse, SystemStatus, MetricGlossaryItem } from '@/api/types';
import { updateDynamicIntervalsFromMeta, subscribeToApiErrors } from '@/api/query-client';
import { useToast } from '@/components/ui/Toast';

export interface MetaContextValue {
  connectionStatus: 'online' | 'offline' | 'checking';
  pipelineVersion?: string;
  asOfDate?: string;
  isStale: boolean;
  meta: MetaResponse | null;
  status: SystemStatus | null;
  glossaryMap: Record<string, MetricGlossaryItem>;
  disclaimersMap: Record<string, string>;
  getMetricDefinition: (metricId: string) => MetricGlossaryItem | undefined;
  getDisclaimer: (key: string) => string | undefined;
  refetchStatus: () => void;
}

export const MetaContext = createContext<MetaContextValue | null>(null);

export function MetaProvider({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();

  // 1. Fetch system status
  const {
    data: statusData,
    isError: statusError,
    isLoading: statusLoading,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: queryKeys.system.status(),
    queryFn: () => apiFetch('/system/status', systemStatusSchema),
    retry: 1,
    refetchInterval: 60 * 1000,
  });

  // 2. Fetch meta endpoint (glossary, disclaimers, intervals)
  const { data: metaData, isError: metaError } = useQuery({
    queryKey: queryKeys.meta.root(),
    queryFn: () => apiFetch('/meta', metaResponseSchema),
    retry: 1,
    staleTime: 60 * 60 * 1000,
  });

  // When meta loads, update query client refresh intervals dynamically
  useEffect(() => {
    if (metaData) {
      updateDynamicIntervalsFromMeta(metaData);
    }
  }, [metaData]);

  // Subscribe to global API errors to dispatch toast notifications
  useEffect(() => {
    const unsubscribe = subscribeToApiErrors((err) => {
      toast({
        title: err.code === 'CONTRACT_MISMATCH' ? 'Contract Error' : 'API Request Failed',
        description: err.message,
        variant: err.code === 'CONTRACT_MISMATCH' ? 'warning' : 'error',
      });
    });
    return unsubscribe;
  }, [toast]);

  const connectionStatus: 'online' | 'offline' | 'checking' = useMemo(() => {
    if (statusLoading) return 'checking';
    if (statusError || metaError) return 'offline';
    if (statusData) return 'online';
    return 'offline';
  }, [statusLoading, statusError, metaError, statusData]);

  // Normalized glossary lookup map
  const glossaryMap = useMemo(() => {
    const map: Record<string, MetricGlossaryItem> = {};
    if (metaData?.metric_glossary) {
      metaData.metric_glossary.forEach((item) => {
        map[item.metric_id] = item;
      });
    }
    return map;
  }, [metaData]);

  const disclaimersMap = useMemo(() => {
    return metaData?.disclaimers ?? {};
  }, [metaData]);

  const value: MetaContextValue = useMemo(
    () => ({
      connectionStatus,
      pipelineVersion: statusData?.pipeline_version || metaData?.version,
      asOfDate: statusData?.as_of_date || metaData?.as_of_date,
      isStale: statusData?.is_stale ?? false,
      meta: metaData ?? null,
      status: statusData ?? null,
      glossaryMap,
      disclaimersMap,
      getMetricDefinition: (id: string) => glossaryMap[id],
      getDisclaimer: (key: string) => disclaimersMap[key],
      refetchStatus,
    }),
    [connectionStatus, statusData, metaData, glossaryMap, disclaimersMap, refetchStatus]
  );

  return <MetaContext.Provider value={value}>{children}</MetaContext.Provider>;
}

export function useMeta() {
  const ctx = useContext(MetaContext);
  if (!ctx) {
    throw new Error('useMeta must be used within a MetaProvider');
  }
  return ctx;
}
