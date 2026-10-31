import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ModelLabNav } from '../components/ModelLabNav';
import { ModelCompareView } from '../components/ModelCompareView';
import { useModelCompareQuery, useModelLeaderboardQuery } from '../hooks/useModelLabData';
import { AlertCircle, RefreshCw, GitCompare } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const DEFAULT_MODELS = [
  'catboost_reg_c_h5',
  'xgboost_reg_c_h5',
  'timesfm_log_returns_ctx64_h5',
  'historical_mean',
];

export default function ModelComparePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlIds = searchParams.get('ids');

  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    if (urlIds) {
      const parts = urlIds.split(',').filter(Boolean);
      if (parts.length > 0) return parts.slice(0, 4);
    }
    return DEFAULT_MODELS;
  });

  // Sync state to URL search parameters
  const handleSelectModelIds = (ids: string[]) => {
    setSelectedIds(ids);
    setSearchParams({ ids: ids.join(',') }, { replace: true });
  };

  useEffect(() => {
    if (urlIds) {
      const parts = urlIds.split(',').filter(Boolean);
      if (parts.length > 0 && parts.join(',') !== selectedIds.join(',')) {
        setSelectedIds(parts.slice(0, 4));
      }
    }
  }, [urlIds, selectedIds]);

  const idsParam = selectedIds.join(',');
  const { data: compareData, isLoading, error, refetch, isFetching } = useModelCompareQuery(idsParam);
  const { data: lbData } = useModelLeaderboardQuery();

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-72" />
        <div className="h-8 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-full max-w-md" />
        <div className="h-64 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
        <div className="h-96 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !compareData) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-lg mx-auto p-6 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Comparison Matrix Unavailable
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {error instanceof Error ? error.message : 'Unable to load model comparison metrics.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" /> Retry Comparison
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header & Sub-Nav */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mb-1">
              <span>Model Lab</span>
              <span>/</span>
              <span className="text-blue-600 dark:text-blue-400 font-semibold">Side-by-Side Comparison</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <GitCompare className="w-7 h-7 text-blue-600 dark:text-blue-400" />
              Side-by-Side Model Comparison
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Directly contrast out-of-sample metrics, walk-forward forecasts, and cross-phase stability for up to 4 models.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="self-start sm:self-auto gap-2 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh Comparison
          </Button>
        </div>

        <ModelLabNav totalModels={lbData?.total_models} />
      </div>

      {/* Comparison View Component */}
      <ModelCompareView
        compareData={compareData}
        allModels={lbData?.leaderboard || []}
        selectedModelIds={selectedIds}
        onSelectModelIds={handleSelectModelIds}
      />
    </div>
  );
}
