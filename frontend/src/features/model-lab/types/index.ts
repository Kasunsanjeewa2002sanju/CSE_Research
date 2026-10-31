import type {
  ModelLeaderboardItem,
  ModelLeaderboardResponse,
  ModelPredictionPoint,
  ModelCumulativeErrorPoint,
  ModelResidualHistogramBin,
  ModelQQPoint,
  ModelResidualDiagnostics,
  ModelFeatureImportance,
  ModelTrainingCurvePoint,
  ModelConfusionMatrix,
  ModelArtifact,
  ModelDetailResponse,
  ModelCompareResponse,
  DieboldMarianoTestItem,
  ModelConfidenceSet,
  FeatureSetAblationItem,
  EventWindowAblationItem,
  ModelStatisticsResponse,
  FinalModelResponse,
} from '@/api/types';

export type {
  ModelLeaderboardItem,
  ModelLeaderboardResponse,
  ModelPredictionPoint,
  ModelCumulativeErrorPoint,
  ModelResidualHistogramBin,
  ModelQQPoint,
  ModelResidualDiagnostics,
  ModelFeatureImportance,
  ModelTrainingCurvePoint,
  ModelConfusionMatrix,
  ModelArtifact,
  ModelDetailResponse,
  ModelCompareResponse,
  DieboldMarianoTestItem,
  ModelConfidenceSet,
  FeatureSetAblationItem,
  EventWindowAblationItem,
  ModelStatisticsResponse,
  FinalModelResponse,
};

export type ModelFamilyFilter = 'all' | 'statistical' | 'shallow' | 'deep' | 'foundation' | 'hybrid' | 'baseline';
export type HorizonFilter = 'all' | '1' | '5';
export type FeatureSetFilter = 'all' | 'A' | 'B' | 'C';
export type MetricSortField = 'oos_r2' | 'directional_accuracy' | 'balanced_accuracy' | 'rmse' | 'mae' | 'theils_u' | 'training_time_s';

export interface LeaderboardFilterState {
  family: ModelFamilyFilter;
  horizon: HorizonFilter;
  featureSet: FeatureSetFilter;
  metric: MetricSortField;
  searchQuery: string;
  onlySignificant: boolean;
}

export type SummaryChartTab = 'metric_bars' | 'phase_heatmap' | 'direction_accuracy' | 'oos_r2' | 'runtime_scatter';
