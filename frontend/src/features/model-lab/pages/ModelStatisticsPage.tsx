import { ModelLabNav } from '../components/ModelLabNav';
import { ModelStatisticsView } from '../components/ModelStatisticsView';
import { useModelStatisticsQuery, useModelLeaderboardQuery } from '../hooks/useModelLabData';
import { AlertCircle, RefreshCw, Award } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function ModelStatisticsPage() {
  const { data: stats, isLoading, error, refetch, isFetching } = useModelStatisticsQuery();
  const { data: lbData } = useModelLeaderboardQuery();

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-72" />
        <div className="h-8 bg-slate-100 dark:bg-slate-800 rounded animate-pulse w-full max-w-md" />
        <div className="h-96 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
        <div className="h-96 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-lg mx-auto p-6 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Statistical Tests Unavailable
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {error instanceof Error ? error.message : 'Unable to load Diebold-Mariano tests and ablation studies.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" /> Retry
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
              <span className="text-blue-600 dark:text-blue-400 font-semibold">Statistical Tests & Ablations</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <Award className="w-7 h-7 text-blue-600 dark:text-blue-400" />
              Econometric Hypotheses & Ablation Testing
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-3xl">
              Pairwise Diebold-Mariano forecast accuracy superiority, Hansen et al. (2011) Model Confidence Set (MCS), Feature Set A vs B vs C paired intervals, and event-window volatility interaction.
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
            Refresh Statistics
          </Button>
        </div>

        <ModelLabNav totalModels={lbData?.total_models} />
      </div>

      {/* Model Statistics View */}
      <ModelStatisticsView stats={stats} />
    </div>
  );
}
