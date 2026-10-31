import { z } from 'zod';

// ============================================================================
// 1. Common & Envelope Schemas
// ============================================================================

export const paginatedQuerySchema = z.object({
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().max(100).default(20),
});

export function paginatedResponseSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive(),
    total_pages: z.number().int().nonnegative(),
    has_next: z.boolean(),
  });
}

// ============================================================================
// 2. Meta, System Health & Status Schemas
// ============================================================================

export const metricGlossaryItemSchema = z.object({
  metric_id: z.string(),
  name: z.string(),
  definition: z.string(),
  formula: z.string().optional(),
  benchmark: z.string().optional(),
  unit: z.string().optional(),
});

export const electionStageItemSchema = z.object({
  id: z.string(),
  stage_number: z.number().int(),
  name: z.string(),
  description: z.string(),
});

export const eventTypeItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
});

export const newsCategoryItemSchema = z.object({
  id: z.string(),
  name: z.string(),
});

export const sectorItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  code: z.string(),
});

export const refreshIntervalsSchema = z.object({
  market_seconds: z.number().positive().default(30),
  events_seconds: z.number().positive().default(3600),
  models_seconds: z.number().positive().default(86400),
  news_seconds: z.number().positive().default(300),
  system_seconds: z.number().positive().default(60),
});

export const projectInfoSchema = z.object({
  title: z.string(),
  institution: z.string(),
  department: z.string(),
  academic_year: z.string(),
  lead_author: z.string().optional(),
  repository_url: z.string().optional(),
});

export const metaResponseSchema = z.object({
  version: z.string(),
  as_of_date: z.string(),
  latest_aspi_value: z.number().optional(),
  latest_aspi_date: z.string().optional(),
  latest_aspi: z.number().optional(),
  categories: z.array(newsCategoryItemSchema).optional(),
  project_info: projectInfoSchema,
  refresh_intervals: refreshIntervalsSchema,
  metric_glossary: z.array(metricGlossaryItemSchema),
  election_stages: z.array(electionStageItemSchema),
  event_types: z.array(eventTypeItemSchema),
  news_categories: z.array(newsCategoryItemSchema),
  sectors: z.array(sectorItemSchema),
  disclaimers: z.record(z.string()),
});

export const systemHealthSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  timestamp: z.string(),
  database: z.string().optional(),
  pipeline: z.string().optional(),
});

export const systemStatusSchema = z.object({
  status: z.string(),
  pipeline_version: z.string(),
  active_stages: z.array(z.number()),
  as_of_date: z.string(),
  is_stale: z.boolean(),
  champion_model: z.string().optional(),
  data_points: z.number().optional(),
  last_pipeline_run: z.string().optional(),
});

// ============================================================================
// 3. Market Series & Summary Schemas
// ============================================================================

export const marketSummarySchema = z.object({
  aspi_level: z.number(),
  daily_return: z.number(),
  five_day_return: z.number().optional(),
  ytd_return: z.number().optional(),
  sp_sl20_level: z.number().optional(),
  sp_sl20_daily_return: z.number().optional(),
  equity_turnover_lkr: z.number(),
  shares_traded: z.number(),
  realized_volatility_annualized: z.number(),
  as_of_date: z.string(),
  is_stale: z.boolean(),
});

export const marketSeriesPointSchema = z.object({
  date: z.string(),
  aspi: z.number(),
  sp_sl20: z.number().nullable().optional(),
  return_pct: z.number().nullable().optional(),
  return: z.number().nullable().optional(),
  turnover_lkr: z.number().nullable().optional(),
  turnover: z.number().nullable().optional(),
  volume: z.number().nullable().optional(),
  realized_vol_20d: z.number().nullable().optional(),
});

export const marketSeriesResponseSchema = z.object({
  series: z.array(marketSeriesPointSchema),
  points: z.array(marketSeriesPointSchema).optional(),
  sample_size: z.number().int().nonnegative().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  disclaimer: z.string().optional(),
  count: z.number().optional(),
  meta: z.any().optional(),
});

export const marketStatsSchema = z.object({
  panel_size_days: z.number().int().nonnegative(),
  as_of_date: z.string(),
  daily_return_pct: z.number().nullable().optional(),
  daily_log_return: z.number().nullable().optional(),
  five_day_return_pct: z.number().nullable().optional(),
  five_day_log_return: z.number().nullable().optional(),
  realized_volatility_annualized: z.number().nullable().optional(),
  volatility_window_days: z.number().optional(),
  annualization_factor: z.number().optional(),
  baseline_aspi: z.number().nullable().optional(),
  baseline_sp20: z.number().nullable().optional(),
  equity_turnover_lkr: z.number().nullable().optional(),
  shares_traded: z.number().nullable().optional(),
  freshness_state: z.string().optional(),
  source_timestamp: z.string().nullable().optional(),
  fetched_at: z.string().optional(),
});

export const marketIntradayPointSchema = z.object({
  timestamp: z.string(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  turnover: z.number().optional(),
  volume: z.number().optional(),
});

export const marketIntradayResponseSchema = z.object({
  metric: z.string(),
  session: z.string(),
  points: z.array(marketIntradayPointSchema),
  count: z.number(),
  downsample_interval: z.string(),
  freshness_state: z.string().optional(),
  source_timestamp: z.string().nullable().optional(),
  fetched_at: z.string().optional(),
});

// ============================================================================
// 4. Data Audit Schemas
// ============================================================================

export const tradingDaysYearSchema = z.object({
  year: z.number().int(),
  trading_days: z.number().int(),
  expected: z.number().int(),
});

export const dictionaryColumnSchema = z.object({
  column: z.string(),
  type: z.string(),
  description: z.string(),
  non_null_count: z.number().int(),
});

export const stationarityTestSchema = z.object({
  test_name: z.string().default('Augmented Dickey-Fuller'),
  test_statistic: z.number(),
  p_value: z.number(),
  is_stationary: z.boolean(),
  critical_values: z.record(z.number()),
});

export const largeMoveItemSchema = z.object({
  date: z.string(),
  return_pct: z.number(),
  flag: z.string(),
  note: z.string().optional(),
});

export const missingnessYearItemSchema = z.object({
  year: z.number().int(),
  aspi_missing: z.number().default(0),
  sp_sl20_missing: z.number().default(0),
  turnover_missing: z.number().default(0),
  volume_missing: z.number().default(0),
});

export const dataAuditSchema = z.object({
  total_records: z.number().int().nonnegative(),
  date_range: z.object({
    start: z.string(),
    end: z.string(),
  }),
  missingness_pct: z.number(),
  jumps_detected: z.number().int(),
  trading_days_per_year: z.array(tradingDaysYearSchema),
  stationarity_adf_test: stationarityTestSchema,
  stationarity_kpss_test: stationarityTestSchema.optional(),
  large_moves: z.array(largeMoveItemSchema).optional(),
  missingness_matrix: z.array(missingnessYearItemSchema).optional(),
  dictionary: z.array(dictionaryColumnSchema),
});

// ============================================================================
// 5. Election Events & Stages Schemas
// ============================================================================

export const eventDetailStageSchema = z.object({
  stage_id: z.string(),
  stage_name: z.string(),
  date: z.string(),
  raw_date: z.string().optional(),
  mapped_date: z.string().optional(),
  rawDate: z.string().optional(),
  mappedTradingDate: z.string().optional(),
  gap_days: z.number().optional(),
  gapDays: z.number().optional(),
  raw_weekday: z.string().optional(),
  mapped_weekday: z.string().optional(),
  is_trading_day_raw: z.boolean().optional(),
  added_by_researcher: z.boolean().optional(),
  is_overlapping: z.boolean().optional(),
  overlapping_details: z.string().optional(),
  significance: z.string().optional(),
  context: z.string().optional(),
  source: z.string().optional(),
  notes: z.string().optional(),
});

export const politicalEventSchema = z.object({
  id: z.string(),
  date: z.string(),
  event_date: z.string().optional(),
  name: z.string(),
  category: z.enum(['Presidential', 'Parliamentary', 'Provincial', 'Crisis', 'Policy', 'All']),
  type: z.string().optional(),
  current_stage: z.string(),
  stage: z.string().optional(),
  rawDate: z.string().optional(),
  mappedTradingDate: z.string().optional(),
  raw_date: z.string().optional(),
  mapped_date: z.string().optional(),
  gapDays: z.number().optional(),
  gap_days: z.number().optional(),
  sample_period: z.boolean().optional(),
  sample_2009_2025: z.boolean().optional(),
  added_by_researcher: z.boolean().optional(),
  is_overlapping: z.boolean().optional(),
  min_dist_other_poll_td: z.number().optional(),
  overlapping_events: z.string().optional(),
  candidate_party_info: z.string().optional(),
  parties: z.array(z.string()).optional(),
  turnout_pct: z.number().optional(),
  margin_pct: z.number().optional(),
  winner_party: z.string().optional(),
  outcome_party: z.string().optional(),
  margin: z.number().optional(),
  turnout: z.number().optional(),
  stages: z.array(eventDetailStageSchema).optional(),
  description: z.string().optional(),
  significance: z.string().optional(),
  context: z.string().optional(),
  aspi_return_event_day: z.number().optional(),
  economic_context: z.string().optional(),
  sources: z.array(z.string()).optional(),
  source_of_information: z.string().optional(),
});

export const eventsListResponseSchema = z.object({
  events: z.array(politicalEventSchema),
  items: z.array(politicalEventSchema).optional(),
  total: z.number().int().nonnegative(),
  count: z.number().int().optional(),
});

export const eventDetailSchema = politicalEventSchema.extend({
  stages: z.array(eventDetailStageSchema),
  economic_context: z.string().optional(),
  outcome_details: z.record(z.unknown()).optional(),
});

export const uncoveredTypeSchema = z.object({
  type: z.string(),
  reason: z.string(),
});

export const eventsCoverageSchema = z.object({
  total_events: z.number().int().nonnegative(),
  total_stages: z.number().int().nonnegative(),
  years_covered: z.string(),
  year_min: z.number().int(),
  year_max: z.number().int(),
  counts_by_type: z.record(z.number()),
  counts_by_stage: z.record(z.number()),
  sample_period_events: z.number().int().nonnegative(),
  overlapping_events: z.number().int().nonnegative(),
  added_by_researcher_events: z.number().int().nonnegative(),
  uncovered_types: z.array(uncoveredTypeSchema),
});

// ============================================================================
// 6. Event Study Results Schemas
// ============================================================================

export const caarDataPointSchema = z.object({
  day: z.number(),
  caar: z.number(),
  ci_lower_95: z.number(),
  ci_upper_95: z.number(),
  ci_lower_80: z.number().optional(),
  ci_upper_80: z.number().optional(),
  ar: z.number().optional(),
  ar_t_stat: z.number().optional(),
  ar_p_val: z.number().optional(),
  sample_size: z.number().int().nonnegative(),
});

export const individualEventCarPointSchema = z.object({
  day: z.number(),
  car: z.number(),
});

export const individualEventStudyPathSchema = z.object({
  event_id: z.string(),
  name: z.string(),
  year: z.number(),
  election_type: z.string(),
  stage: z.string(),
  date: z.string(),
  car: z.number(),
  path: z.array(individualEventCarPointSchema),
});

export const permutationBinSchema = z.object({
  min: z.number(),
  max: z.number(),
  count: z.number(),
});

export const permutationDistributionSchema = z.object({
  bins: z.array(permutationBinSchema),
  observed_value: z.number(),
  p_value: z.number(),
  draws: z.number().optional(),
});

export const caarStatsSchema = z.object({
  caar: z.number(),
  median_car: z.number().optional(),
  std_car: z.number().optional(),
  t_stat: z.number().optional(),
  t_pval: z.number().optional(),
  t_pval_bh: z.number().optional(),
  permutation_pval: z.number().optional(),
  sign_test_pval: z.number().optional(),
  significance_badge: z.string().optional(),
});

export const eventStudyCaarResponseSchema = z.object({
  window_days: z.string(),
  election_type: z.string().optional(),
  stage: z.string().optional(),
  model_type: z.string().optional(),
  estimation_len: z.number().optional(),
  include_overlapping: z.boolean().optional(),
  event_count: z.number().int(),
  warn_small_sample: z.boolean().optional(),
  small_sample_warning_text: z.string().optional(),
  sample_size_threshold: z.number().optional(),
  caar_stats: caarStatsSchema.optional(),
  data: z.array(caarDataPointSchema),
  individual_events: z.array(individualEventStudyPathSchema).optional(),
  permutation_distribution: permutationDistributionSchema.optional(),
  modelled_trajectory: z.record(z.unknown()).nullable().optional(),
  p_value_permutation: z.number(),
  p_value_bonferroni: z.number().optional(),
  statistical_significance: z.boolean(),
  as_of_date: z.string(),
});

export const eventStudySubgroupSchema = z.object({
  category: z.string(),
  event_count: z.number().int(),
  mean_car_event_day: z.number(),
  caar_window_pct: z.number(),
  p_value: z.number(),
});

export const eventStudySubgroupsResponseSchema = z.object({
  subgroups: z.array(eventStudySubgroupSchema),
  window_days: z.string().optional(),
});

export const heatmapCellSchema = z.object({
  election_type: z.string(),
  stage: z.string(),
  window: z.string(),
  caar: z.number(),
  median_car: z.number().optional(),
  std_car: z.number().optional(),
  t_stat: z.number().optional(),
  t_pval: z.number().optional(),
  t_pval_bh: z.number().optional(),
  sign_test_pval: z.number().optional(),
  wilcoxon_pval_bh: z.number().optional(),
  n: z.number().int(),
  warn_small_sample: z.boolean().optional(),
  is_significant: z.boolean().optional(),
});

export const eventStudyHeatmapResponseSchema = z.object({
  cells: z.array(heatmapCellSchema),
  windows: z.array(z.string()),
  election_types: z.array(z.string()),
  stages: z.array(z.string()),
  total_cells: z.number().int().optional(),
});

export const eventStudyPerEventItemSchema = z.object({
  event_id: z.string(),
  event_name: z.string(),
  election_type: z.string(),
  stage: z.string(),
  date: z.string(),
  raw_date: z.string().optional(),
  year: z.number().int(),
  window: z.string(),
  car: z.number(),
  bw_se: z.number(),
  ci_lower: z.number(),
  ci_upper: z.number(),
  t_stat: z.number(),
  p_value: z.number(),
  permutation_p_val: z.number(),
  corrected_p_val: z.number(),
  is_overlapping: z.boolean(),
  aspi_before: z.number(),
  aspi_after: z.number(),
  change_pct: z.number(),
  significance_badge: z.string().optional(),
});

export const eventStudyPerEventResponseSchema = z.object({
  items: z.array(eventStudyPerEventItemSchema),
  total: z.number().int(),
  window: z.string(),
});

export const eventStudySummaryResponseSchema = z.object({
  summary_markdown: z.string(),
  methodology: z.string(),
  caveats: z.array(z.string()),
  small_sample_threshold: z.number(),
  disclaimer: z.string(),
});

// ============================================================================
// 7. Research Protocol & Feature Dictionary Schemas
// ============================================================================

export const protocolPhaseSchema = z.object({
  phase_id: z.string(),
  name: z.string(),
  start_date: z.string(),
  end_date: z.string(),
  train_start: z.string().optional(),
  train_end: z.string().optional(),
  train_days: z.number().int().optional(),
  embargo_start: z.string().optional(),
  embargo_end: z.string().optional(),
  embargo_days: z.number().int().optional(),
  val_start: z.string().optional(),
  val_end: z.string().optional(),
  val_days: z.number().int().optional(),
  inner_train_days: z.number().int().optional(),
  inner_embargo_days: z.number().int().optional(),
  inner_val_days: z.number().int().optional(),
  total_days: z.number().int().optional(),
  description: z.string(),
  sample_size: z.number().int(),
});

export const leakageTestStatusSchema = z.object({
  status: z.enum(['passed', 'warning', 'failed']),
  last_checked: z.string(),
  checks_performed: z.array(z.string()),
  failed_checks: z.array(z.string()),
});

export const targetDefinitionSchema = z.object({
  target_id: z.string(),
  name: z.string().optional(),
  formula: z.string(),
  horizon_days: z.number().int(),
  horizon_label: z.string().optional(),
  return_formula: z.string().optional(),
  direction_formula: z.string().optional(),
  direction_target: z.string().optional(),
  description: z.string().optional(),
});

export const leakageTestItemSchema = z.object({
  test_id: z.string(),
  name: z.string(),
  status: z.enum(['passed', 'warning', 'failed']),
  plain_language_meaning: z.string(),
  last_run_time: z.string(),
  scope: z.string().optional(),
  tolerance: z.string().optional(),
  verdict_details: z.string().optional(),
});

export const pipelineStageSchema = z.object({
  stage_id: z.string(),
  stage_number: z.number().int(),
  name: z.string(),
  category: z.string(),
  status: z.enum(['completed', 'ready', 'running', 'failed']),
  last_run_time: z.string(),
  report_url: z.string(),
  report_title: z.string(),
  summary: z.string(),
  dependencies: z.array(z.string()),
});

export const baselineDefinitionSchema = z.object({
  id: z.string(),
  name: z.string(),
  formula: z.string(),
  direction_rule: z.string(),
  definition: z.string(),
  interpretation: z.string(),
  benchmark_role: z.string(),
});

export const protocolResponseSchema = z.object({
  phases: z.array(protocolPhaseSchema),
  embargo_rules: z.array(
    z.object({
      rule: z.string(),
      rationale: z.string(),
    })
  ),
  target_definitions: z.array(targetDefinitionSchema),
  leakage_test_status: leakageTestStatusSchema,
  leakage_tests: z.array(leakageTestItemSchema).optional(),
  pipeline_stages: z.array(pipelineStageSchema).optional(),
  baselines: z.array(baselineDefinitionSchema).optional(),
});

export const phaseEventCoverageItemSchema = z.object({
  phase: z.string(),
  val_dates: z.string(),
  val_days_total: z.number().int(),
  days_in_active_stage: z.number().int(),
  pct_in_active_stage: z.string(),
  days_in_win_0_2: z.number().int(),
  days_in_win_0_7: z.number().int(),
  days_in_win_0_15: z.number().int(),
  days_in_win_0_30: z.number().int(),
  pct_in_win_0_30: z.string(),
});

export const featureDictionaryItemSchema = z.object({
  feature_name: z.string(),
  feature_sets: z.array(z.string()).optional(),
  category: z.string(),
  group: z.enum(['price', 'activity', 'event']).optional(),
  dtype: z.string().optional(),
  description: z.string(),
  availability: z.string().optional(),
  lookahead_check: z.string().optional(),
  lag_days: z.number().int().nonnegative(),
  source: z.string(),
  stationarity: z.boolean(),
});

export const featureDictionaryResponseSchema = z.object({
  total_features: z.number().int(),
  features: z.array(featureDictionaryItemSchema),
  phase_event_coverage: z.array(phaseEventCoverageItemSchema).optional(),
});

// ============================================================================
// 8. Machine Learning & Model Lab Schemas
// ============================================================================


export const predictionItemSchema = z.object({
  date: z.string(),
  actual_return: z.number(),
  predicted_return: z.number(),
  residual: z.number(),
  ci_lower: z.number().optional(),
  ci_upper: z.number().optional(),
});

export const modelPredictionsResponseSchema = z.object({
  model_id: z.string(),
  horizon: z.number().int(),
  predictions: z.array(predictionItemSchema),
});

export const dmTestPairSchema = z.object({
  model_a: z.string(),
  model_b: z.string(),
  statistic: z.number(),
  p_value: z.number(),
  preferred_model: z.string(),
  significant: z.boolean(),
});

export const dmTestMatrixResponseSchema = z.object({
  matrix: z.array(dmTestPairSchema),
});

export const ablationResponseSchema = z.object({
  feature_set_ablation: z.array(
    z.object({
      set_name: z.string(),
      description: z.string(),
      features_included: z.number().int(),
      oos_r2: z.number(),
      delta_vs_full: z.number(),
    })
  ),
  window_ablation: z.array(
    z.object({
      window_name: z.string(),
      days: z.number().int(),
      oos_r2: z.number(),
      rmse: z.number(),
    })
  ),
});

export const modelArtifactItemSchema = z.object({
  name: z.string(),
  file_size_bytes: z.number().int(),
  updated_at: z.string(),
  sha256: z.string().optional(),
  download_url: z.string().optional(),
});

export const modelArtifactsResponseSchema = z.object({
  artifacts: z.array(modelArtifactItemSchema),
});

// ============================================================================
// 9. Live News & RSS Feed Schemas
// ============================================================================

export const duplicateClusterItemSchema = z.object({
  id: z.string(),
  headline: z.string(),
  source: z.string(),
  url: z.string(),
  published_at: z.string().optional(),
});

export const newsFiltersSchema = z.object({
  sources: z.array(z.string()),
  categories: z.array(z.string()),
  stages: z.array(z.string()),
  languages: z.array(z.string()),
  evidence_strengths: z.array(z.string()),
  relevance_options: z.array(z.string()),
});

export const newsItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  headline: z.string().optional(),
  description: z.string().optional(),
  published_at: z.string(),
  publishedAt: z.string().optional(),
  source: z.string(),
  url: z.string(),
  image_url: z.string().nullable().optional(),
  sentiment_score: z.number().optional(),
  tags: z.array(z.string()).optional(),
  category: z.string(),
  stage: z.string().optional(),
  direction: z.string().optional(),
  confidence: z.number().optional(),
  language: z.string().optional(),
  is_relevant: z.boolean().optional(),
  evidence_strength: z.string().optional(),
  reason: z.string().optional(),
  entities: z.array(z.string()).optional(),
  affected_sectors: z.array(z.string()).optional(),
  duplicate_cluster: z.array(duplicateClusterItemSchema).optional(),
  diff_h1: z.number().optional(),
  diff_h5: z.number().optional(),
  prob_up_h1: z.number().optional(),
  prob_up_h5: z.number().optional(),
});

export const newsItemsResponseSchema = z.object({
  items: z.array(newsItemSchema),
  total: z.number().int().nonnegative(),
  count: z.number().int().nonnegative().optional(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  total_pages: z.number().int().nonnegative(),
  has_next: z.boolean(),
  filters: newsFiltersSchema.optional(),
});

export const newsItemDetailResponseSchema = z.object({
  item: newsItemSchema,
});

export const newsFeedItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  url: z.string(),
  status: z.enum(['active', 'degraded', 'error']).or(z.string()),
  status_code: z.number().int().optional(),
  is_active: z.boolean().optional(),
  last_polled_at: z.string(),
  article_count_24h: z.number().int().nonnegative(),
  response_time_sec: z.number().optional(),
  error_count: z.number().int().nonnegative().optional(),
  last_error: z.string().nullable().optional(),
  feed_type: z.string().optional(),
});

export const newsFeedsResponseSchema = z.object({
  feeds: z.array(newsFeedItemSchema),
});

export const pipelineRunItemSchema = z.object({
  run_id: z.string(),
  started_at: z.string(),
  completed_at: z.string().optional(),
  status: z.enum(['completed', 'failed', 'running']).or(z.string()),
  articles_ingested: z.number().int().nonnegative(),
  duration_sec: z.number().optional(),
  error_message: z.string().optional(),
});

export const pipelineRunsResponseSchema = z.object({
  runs: z.array(pipelineRunItemSchema),
});

export const failureLogItemSchema = z.object({
  feed_name: z.string(),
  url: z.string(),
  status: z.string(),
  status_code: z.number().int(),
  error_message: z.string(),
  last_checked: z.string(),
  severity: z.enum(['critical', 'warning']).or(z.string()),
});

export const itemsPerHourItemSchema = z.object({
  hour: z.string(),
  total: z.number(),
  by_source: z.record(z.string(), z.number()),
});

export const classificationDistributionItemSchema = z.object({
  category: z.string(),
  label: z.string(),
  count: z.number(),
  percentage: z.number(),
});

export const languageSplitItemSchema = z.object({
  language: z.string(),
  label: z.string(),
  count: z.number(),
  percentage: z.number(),
});

export const relevanceFunnelStageSchema = z.object({
  stage: z.string(),
  label: z.string(),
  count: z.number(),
  percentage: z.number(),
  description: z.string(),
});

export const relevanceFunnelSchema = z.object({
  stages: z.array(relevanceFunnelStageSchema),
  conversion_rate_pct: z.number(),
  deduplication_rate_pct: z.number(),
});

export const pipelineStatsSummarySchema = z.object({
  total_ingested_items: z.number(),
  relevant_items: z.number(),
  active_feeds: z.number(),
  degraded_feeds: z.number(),
  error_feeds: z.number(),
  total_feeds: z.number(),
  last_ingested_at: z.string(),
  sources_count: z.number(),
});

export const pipelineStatsResponseSchema = z.object({
  summary: pipelineStatsSummarySchema,
  feed_health: z.object({
    total: z.number(),
    active: z.number(),
    degraded: z.number(),
    error: z.number(),
  }),
  items_per_hour_by_source: z.array(itemsPerHourItemSchema),
  classification_distribution: z.array(classificationDistributionItemSchema),
  relevance_funnel: relevanceFunnelSchema,
  language_split: z.array(languageSplitItemSchema),
  run_history: z.array(pipelineRunItemSchema),
  failures_log: z.array(failureLogItemSchema),
});

// ============================================================================
// 10. Scenario Predictor Schemas (Stage F9)
// ============================================================================

export const scenarioSubmitRequestSchema = z.object({
  headline: z.string().min(3, 'Headline must be at least 3 characters'),
  description: z.string().optional().default(''),
  publication_date: z.string().optional().default(''),
  date: z.string().optional(),
  category: z.string().optional(),
  sector: z.string().optional(),
  source: z.string().optional(),
  current_aspi: z.number().positive().optional(),
});

// Backward compatibility alias
export const scenarioPredictRequestSchema = z.object({
  event_type: z.string().optional(),
  expected_turnout_pct: z.number().min(0).max(100).optional(),
  expected_margin_pct: z.number().min(0).max(100).optional(),
  lead_party: z.string().optional(),
  market_regime: z.enum(['bull', 'bear', 'neutral']).default('neutral'),
  horizon_days: z.number().int().positive().default(5),
  headline: z.string().optional(),
  description: z.string().optional(),
  publication_date: z.string().optional(),
  date: z.string().optional(),
  category: z.string().optional(),
  sector: z.string().optional(),
});

export const scenarioHorizonSchema = z.object({
  horizon_days: z.number(),
  expected_return: z.number(),
  expected_return_pct: z.number(),
  target_aspi: z.number(),
  probability_up: z.number(),
  trend_direction: z.string(),
  trend_arrow: z.string(),
  trend_sign: z.string(),
  interval_80: z.array(z.number()),
  interval_95: z.array(z.number()),
  interval_80_ret: z.array(z.number()).optional(),
  interval_95_ret: z.array(z.number()).optional(),
  is_magnitude_capped: z.boolean().optional(),
});

export const scenarioPanelSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  primary_horizon: z.number(),
  expected_return: z.number(),
  expected_return_pct: z.number(),
  target_aspi: z.number(),
  probability_up: z.number(),
  trend_direction: z.string(),
  trend_arrow: z.string(),
  trend_sign: z.string(),
  interval_80: z.array(z.number()),
  interval_95: z.array(z.number()),
  interval_80_ret: z.array(z.number()).optional(),
  interval_95_ret: z.array(z.number()).optional(),
  horizons: z.record(z.string(), scenarioHorizonSchema).optional(),
  sparkline: z.array(z.number()),
});

export const scenarioCarPointSchema = z.object({
  day: z.number(),
  caar: z.number(),
  ci_lower_95: z.number().optional(),
  ci_upper_95: z.number().optional(),
  ci_lower_80: z.number().optional(),
  ci_upper_80: z.number().optional(),
});

export const scenarioEvidenceSchema = z.object({
  has_historical_match: z.boolean(),
  matching_type: z.string(),
  matching_stage: z.string(),
  window: z.string(),
  n_events: z.number(),
  mean_car: z.number(),
  median_car: z.number().optional(),
  std_car: z.number().optional(),
  t_statistic: z.number().optional(),
  t_pvalue: z.number().optional(),
  sign_test_pvalue: z.number().optional(),
  permutation_pvalue: z.number().optional(),
  small_sample_warning: z.boolean().optional(),
  evidence_strength: z.string(),
  evidence_strength_text: z.string(),
  car_series: z.array(scenarioCarPointSchema).optional(),
  meaning_of_false: z.string().optional(),
});

export const scenarioComparisonColumnSchema = z.object({
  key: z.string(),
  label: z.string(),
});

export const scenarioComparisonRowSchema = z.object({
  metric: z.string(),
  current: z.string(),
  true_val: z.string(),
  false_val: z.string(),
  net_diff: z.string(),
});

export const scenarioComparisonMatrixSchema = z.object({
  columns: z.array(scenarioComparisonColumnSchema),
  rows: z.array(scenarioComparisonRowSchema),
});

export const scenarioHistoryPointSchema = z.object({
  date: z.string(),
  aspi: z.number(),
});

export const scenarioFanChartPointSchema = z.object({
  horizon: z.number(),
  target_aspi: z.number(),
  ci80_lower: z.number(),
  ci80_upper: z.number(),
  ci95_lower: z.number(),
  ci95_upper: z.number(),
});

export const scenarioFanChartSchema = z.object({
  as_of_date: z.string(),
  current_aspi: z.number(),
  horizons: z.array(z.number()),
  true_scenario: z.array(scenarioFanChartPointSchema),
  false_scenario: z.array(scenarioFanChartPointSchema),
});

export const scenarioSubmitResponseSchema = z.object({
  scenario_id: z.string(),
  status: z.string(),
  headline: z.string(),
  description: z.string().optional(),
  publication_date: z.string(),
  as_of_date: z.string(),
  current_aspi: z.number(),
  is_stale: z.boolean(),
  stale_warning: z.string().nullable().optional(),
  meaning_of_false: z.string(),
  disclaimer: z.string(),
  category: z.string(),
  category_label: z.string(),
  stage: z.string(),
  stage_label: z.string(),
  expected_direction: z.string(),
  expected_direction_arrow: z.string(),
  expected_direction_sign: z.string(),
  evidence_strength: z.string(),
  evidence_strength_text: z.string(),
  is_material_impact: z.boolean(),
  material_impact_summary: z.string(),
  scenarios: z.object({
    CURRENT: scenarioPanelSchema,
    TRUE: scenarioPanelSchema,
    FALSE: scenarioPanelSchema,
  }),
  impact: z.record(z.string(), z.any()).optional(),
  comparison_matrix: scenarioComparisonMatrixSchema,
  recent_history: z.array(scenarioHistoryPointSchema).optional(),
  fan_chart: scenarioFanChartSchema.optional(),
  historical_evidence: scenarioEvidenceSchema,
  explanation: z.string(),
});

// Backward compatibility response schema alias
export const scenarioPredictResponseSchema = z.object({
  scenario_id: z.string(),
  predicted_aspi_impact_pct: z.number().optional(),
  confidence_interval_95: z.tuple([z.number(), z.number()]).optional(),
  confidence_interval_80: z.tuple([z.number(), z.number()]).optional(),
  historical_analogues: z.array(
    z.object({
      event_name: z.string(),
      year: z.number().int(),
      realized_impact_pct: z.number(),
    })
  ).optional(),
  explanation: z.string(),
  disclaimer: z.string(),
  // Extended fields from scenarioSubmitResponseSchema when returned
  scenarios: z.any().optional(),
  meaning_of_false: z.string().optional(),
  evidence_strength: z.string().optional(),
  expected_direction: z.string().optional(),
  is_stale: z.boolean().optional(),
  stale_warning: z.string().nullable().optional(),
});

export const scenarioBacktestItemSchema = z.object({
  scenario_name: z.string(),
  date: z.string(),
  target_date: z.string().optional(),
  horizon_h: z.number().optional(),
  aspi_baseline: z.number().optional(),
  predicted_aspi: z.number().optional(),
  actual_aspi: z.number().optional(),
  predicted_impact_pct: z.number(),
  actual_impact_pct: z.number(),
  error_pct: z.number(),
  hit_direction: z.boolean().optional(),
  status: z.string().optional(),
  inside_ci_80: z.boolean().optional(),
  inside_ci_95: z.boolean(),
});

export const scenarioBacktestsSummarySchema = z.object({
  total_tests: z.number(),
  hits: z.number(),
  misses: z.number(),
  hit_rate_pct: z.number(),
  coverage_80_pct: z.number().optional(),
  coverage_95_pct: z.number(),
  mean_absolute_error_pct: z.number(),
});

export const scenarioBacktestsResponseSchema = z.object({
  summary: scenarioBacktestsSummarySchema.optional(),
  backtests: z.array(scenarioBacktestItemSchema),
  disclaimer: z.string().optional(),
});

// ============================================================================
// 11. Research Artifacts, Audit & Exports Schemas
// ============================================================================

export const researchDocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string(),
  file_type: z.string(),
  last_updated: z.string(),
  url: z.string(),
  description: z.string(),
});

export const researchIndexResponseSchema = z.object({
  documents: z.array(researchDocumentSchema),
});

export const auditDimensionSchema = z.object({
  dimension: z.string(),
  score: z.number(),
  verdict: z.string(),
  details: z.string(),
});

export const researchAuditReportResponseSchema = z.object({
  audit_passed: z.boolean(),
  dimensions_verified: z.array(auditDimensionSchema),
  generated_at: z.string(),
});

export const researchExportItemSchema = z.object({
  export_id: z.string(),
  name: z.string(),
  format: z.enum(['csv', 'json', 'parquet']),
  endpoint: z.string(),
  row_count: z.number().int().optional(),
});

export const researchExportsResponseSchema = z.object({
  available_exports: z.array(researchExportItemSchema),
});

// ============================================================================
// 12. User Favorites & SUS Survey Schemas
// ============================================================================

export const favoriteItemSchema = z.object({
  id: z.string(),
  item_type: z.enum(['event', 'model', 'figure', 'table']),
  title: z.string(),
  target_url: z.string(),
  saved_at: z.string(),
});

export const favoritesResponseSchema = z.object({
  favorites: z.array(favoriteItemSchema),
});

export const susQuestionSchema = z.object({
  id: z.number().int(),
  prompt: z.string(),
  polarity: z.enum(['positive', 'negative']),
});

export const susSurveyResponseSchema = z.object({
  version: z.string(),
  questions: z.array(susQuestionSchema),
});

// ============================================================================
// 13. Model Lab, Leaderboard & Diagnostics Schemas (Stage F7)
// ============================================================================

export const modelLeaderboardItemSchema = z.object({
  model_id: z.string(),
  model_name: z.string(),
  family: z.enum(['statistical', 'shallow', 'deep', 'foundation', 'hybrid', 'baseline']),
  feature_set: z.string(),
  horizon: z.number().int(),
  is_baseline: z.boolean(),
  is_champion: z.boolean(),
  rank_overall: z.number().int(),
  rank_family: z.number().int(),
  oos_r2_mean: z.number(),
  oos_r2_std: z.number(),
  oos_r2_phases: z.record(z.number()),
  accuracy_mean: z.number(),
  accuracy_std: z.number(),
  accuracy_ci_lower: z.number(),
  accuracy_ci_upper: z.number(),
  accuracy_phases: z.record(z.number()),
  balanced_accuracy_mean: z.number(),
  balanced_accuracy_std: z.number(),
  rmse_mean: z.number(),
  rmse_std: z.number(),
  mae_mean: z.number(),
  mae_std: z.number(),
  theils_u_mean: z.number(),
  theils_u_std: z.number(),
  training_time_s: z.number(),
  parameters: z.union([z.string(), z.number()]),
  significantly_better_than_baseline: z.boolean(),
  significance_correction_method: z.string(),
  p_value_vs_baseline: z.number(),
  correction_details: z.string().optional(),
});

export const modelLeaderboardResponseSchema = z.object({
  leaderboard: z.array(modelLeaderboardItemSchema),
  total_models: z.number().int(),
  baseline_models: z.array(z.string()),
  champion_model_id: z.string(),
  any_model_beats_baseline: z.boolean(),
  summary_message: z.string(),
  as_of_date: z.string(),
  evaluation_protocol: z.string(),
  disclaimer: z.string(),
});

export const modelPredictionPointSchema = z.object({
  date: z.string(),
  actual_return: z.number(),
  predicted_return: z.number(),
  residual: z.number(),
  ci_lower: z.number().optional(),
  ci_upper: z.number().optional(),
  is_validation: z.boolean().optional(),
  phase: z.string().optional(),
});

export const modelCumulativeErrorPointSchema = z.object({
  date: z.string(),
  cumulative_mae: z.number(),
  cumulative_rmse: z.number(),
});

export const modelResidualHistogramBinSchema = z.object({
  bin_start: z.number(),
  bin_end: z.number(),
  count: z.number().int(),
  density: z.number(),
});

export const modelQQPointSchema = z.object({
  theoretical_quantile: z.number(),
  sample_quantile: z.number(),
});

export const modelResidualDiagnosticsSchema = z.object({
  histogram: z.array(modelResidualHistogramBinSchema),
  qq_plot: z.array(modelQQPointSchema),
  mean: z.number(),
  std: z.number(),
  skewness: z.number(),
  kurtosis: z.number(),
  lb_stat_lag5: z.number(),
  lb_pval_lag5: z.number(),
  is_white_noise: z.boolean(),
});

export const modelFeatureImportanceSchema = z.object({
  feature: z.string(),
  importance: z.number(),
  category: z.string().optional(),
});

export const modelTrainingCurvePointSchema = z.object({
  iteration: z.number().int(),
  train_loss: z.number(),
  val_loss: z.number(),
});

export const modelConfusionMatrixSchema = z.object({
  true_positive: z.number().int(),
  false_positive: z.number().int(),
  false_negative: z.number().int(),
  true_negative: z.number().int(),
  accuracy: z.number(),
  precision: z.number(),
  recall: z.number(),
  f1_score: z.number(),
  mcc: z.number(),
});

export const modelArtifactSchema = z.object({
  name: z.string(),
  file_size_bytes: z.number(),
  updated_at: z.string(),
  sha256: z.string(),
  download_url: z.string(),
});

export const modelDetailResponseSchema = z.object({
  model_id: z.string(),
  model_name: z.string(),
  family: z.string(),
  feature_set: z.string(),
  horizon: z.number().int(),
  hyperparameters: z.record(z.any()),
  training_data_range: z.array(z.string()),
  seed: z.number().int(),
  hardware: z.string(),
  runtime_seconds: z.number(),
  memory_mb: z.number(),
  per_phase_predictions: z.array(modelPredictionPointSchema),
  cumulative_error: z.array(modelCumulativeErrorPointSchema),
  residuals: modelResidualDiagnosticsSchema,
  feature_importance: z.array(modelFeatureImportanceSchema),
  training_curves: z.array(modelTrainingCurvePointSchema),
  confusion_matrix: modelConfusionMatrixSchema,
  artifacts: z.array(modelArtifactSchema),
});

export const modelCompareResponseSchema = z.object({
  compared_models: z.array(modelLeaderboardItemSchema),
  forecast_comparison: z.array(z.record(z.any())),
  phase_stability: z.array(z.record(z.any())),
});

export const dieboldMarianoTestItemSchema = z.object({
  model_a: z.string(),
  model_b: z.string(),
  statistic: z.number(),
  p_value: z.number(),
  significant: z.boolean(),
  preferred_model: z.string(),
});

export const modelConfidenceSetSchema = z.object({
  confidence_level: z.number(),
  included_models: z.array(z.record(z.any())),
  excluded_models: z.array(z.record(z.any())),
});

export const featureSetAblationItemSchema = z.object({
  architecture: z.string(),
  family: z.string(),
  horizon: z.number().int(),
  n_samples: z.number().int(),
  r2_set_a: z.number(),
  r2_set_b: z.number(),
  r2_set_c: z.number(),
  delta_r2_c_minus_a: z.number(),
  delta_r2_c_minus_b: z.number(),
  acc_set_a: z.number(),
  acc_set_b: z.number(),
  acc_set_c: z.number(),
  t_stat_c_vs_a: z.number(),
  p_val_c_vs_a: z.number(),
  t_stat_c_vs_b: z.number(),
  p_val_c_vs_b: z.number(),
});

export const eventWindowAblationItemSchema = z.object({
  model: z.string(),
  family: z.string(),
  horizon: z.number().int(),
  phase: z.string(),
  n_inside_events: z.number().int(),
  n_outside_events: z.number().int(),
  r2_inside: z.number(),
  r2_outside: z.number(),
  delta_r2_in_minus_out: z.number(),
  acc_inside: z.number(),
  acc_outside: z.number(),
  delta_acc_in_minus_out: z.number(),
  pt_pval_inside: z.number(),
});

export const modelStatisticsResponseSchema = z.object({
  dm_matrix: z.array(dieboldMarianoTestItemSchema),
  matrix_models: z.array(z.string()),
  model_confidence_set: modelConfidenceSetSchema,
  ablation_feature_sets: z.array(featureSetAblationItemSchema),
  ablation_event_windows: z.array(eventWindowAblationItemSchema),
});

export const finalModelResponseSchema = z.object({
  model_id: z.string(),
  model_name: z.string(),
  family: z.string(),
  architecture: z.string(),
  version: z.string(),
  release_date: z.string(),
  license: z.string(),
  training_data_range: z.array(z.string()),
  n_training_samples: z.number().int(),
  n_features: z.number().int(),
  primary_target: z.string(),
  secondary_target: z.string(),
  hyperparameters: z.record(z.any()),
  empirical_metrics: z.record(z.any()),
  top_features: z.array(z.any()),
  selection_hierarchy: z.array(z.string()),
  limitations: z.array(z.string()),
  selection_verdict: z.string(),
  model_card_markdown: z.string(),
  decision_trace_markdown: z.string(),
});
