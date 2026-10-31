import { useParams, useNavigate } from 'react-router-dom';
import { ModelLabNav } from '../components/ModelLabNav';
import { ModelDetailForecast } from '../components/ModelDetailForecast';
import { ModelDetailDiagnostics } from '../components/ModelDetailDiagnostics';
import { useModelDetailQuery, useModelLeaderboardQuery } from '../hooks/useModelLabData';
import { AlertCircle, RefreshCw, HelpCircle, ArrowLeft, GitCompare } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function ModelDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const modelId = id || 'catboost_reg_c_h5';

  const { data: detail, isLoading, error, refetch, isFetching } = useModelDetailQuery(modelId);
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

  if (error || !detail) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-lg mx-auto p-6 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Model Diagnostics Unavailable
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {error instanceof Error ? error.message : `Unable to find model diagnostics for "${modelId}".`}
          </p>
          <div className="flex items-center justify-center gap-3">
            <Button onClick={() => navigate('/models')} variant="outline" className="gap-2">
              <ArrowLeft className="w-4 h-4" /> Return to Leaderboard
            </Button>
            <Button onClick={() => refetch()} variant="primary" className="gap-2">
              <RefreshCw className="w-4 h-4" /> Retry
            </Button>
          </div>
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
              <button
                onClick={() => navigate('/models')}
                className="hover:text-blue-600 dark:hover:text-blue-400 underline underline-offset-2"
              >
                Leaderboard
              </button>
              <span>/</span>
              <span className="text-blue-600 dark:text-blue-400 font-semibold">{modelId}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <HelpCircle className="w-7 h-7 text-blue-600 dark:text-blue-400" />
              {detail.model_name}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Family: <span className="font-semibold text-slate-800 dark:text-slate-200">{detail.family}</span> &bull; Horizon: <span className="font-semibold text-slate-800 dark:text-slate-200">h={detail.horizon}</span> &bull; Feature Set: <span className="font-semibold text-slate-800 dark:text-slate-200">Set {detail.feature_set}</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
            {/* Quick model selector */}
            {lbData && lbData.leaderboard.length > 0 && (
              <select
                value={modelId}
                onChange={(e) => navigate(`/models/${e.target.value}`)}
                className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 font-mono"
                aria-label="Switch model diagnostics"
              >
                {lbData.leaderboard.map((m) => (
                  <option key={m.model_id} value={m.model_id}>
                    {m.model_name} (h={m.horizon}, Set {m.feature_set})
                  </option>
                ))}
              </select>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/models/compare?ids=${modelId},historical_mean`)}
              className="gap-1.5 text-xs"
            >
              <GitCompare className="w-3.5 h-3.5" />
              Compare vs Baseline
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="gap-1.5 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        <ModelLabNav totalModels={lbData?.total_models} activeModelId={modelId} />
      </div>

      {/* 1. Hardware, Hyperparameters, Forecast vs Actual & Cumulative Error */}
      <ModelDetailForecast detail={detail} />

      {/* 2. Residuals, QQ Plot, Confusion Matrix, Feature Importance / Curves & Artifacts */}
      <ModelDetailDiagnostics detail={detail} />
    </div>
  );
}
