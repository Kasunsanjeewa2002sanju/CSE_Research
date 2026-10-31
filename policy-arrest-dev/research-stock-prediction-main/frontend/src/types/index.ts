export interface StockPoint {
  date: string;
  aspi: number | null;
  sp_sl20: number | null;
  turnover_mn: number | null;
  daily_return_pct: number;
}

export interface EventMarker {
  event_id: string;
  title: string;
  event_family: 'Government Policy' | 'Political Arrest';
  event_subtype: string;
  aligned_date: string;
  aspi_close_event: number;
  car_1d: number;
  car_5d: number;
  car_20d: number;
  raw_return_5d: number;
  impact_direction: 'Positive' | 'Negative' | 'Neutral';
}

export interface TimelineResponse {
  date_range: { from: string; to: string };
  total_sessions: number;
  total_events_in_range: number;
  price_series: StockPoint[];
  event_markers: EventMarker[];
}

export interface PricePathPoint {
  relative_day: number;
  date: string;
  aspi_close: number;
  pct_change_from_event: number;
}

export interface EventDetail {
  event_id: string;
  title: string;
  event_family: string;
  event_subtype: string;
  aligned_date: string;
  aspi_close_event: number;
  mean_expected_daily_return: number;
  estimation_volatility: number;
  ar_day_0: number;
  ret_day_0: number;
  raw_return_1d: number;
  raw_return_5d: number;
  raw_return_20d: number;
  car_0_1: number;
  car_0_5: number;
  car_0_20: number;
  car_pre_5d: number;
  max_drawdown_20d: number;
  turnover_shock_ratio: number;
  impact_direction: string;
  summary?: string;
  sources?: Array<{ name: string; url: string }>;
  cluster_id?: string;
  is_duplicate?: boolean;
  affected_sectors?: string;
  expected_channel?: string;
  main_person?: string;
  political_party?: string;
  government_or_opposition?: string;
  price_path: PricePathPoint[];
  interpretation_notice: string;
}

export interface AnalogueEvent {
  event_id: string;
  title: string;
  aligned_date: string;
  event_family: string;
  event_subtype: string;
  similarity_score: number;
  car_1d: number;
  car_5d: number;
  car_20d: number;
  raw_return_5d: number;
  impact_direction: string;
  mini_price_path?: Array<{ relative_day: number; pct_change: number }>;
}

export interface FanChartPoint {
  trading_day: number;
  date: string;
  baseline_no_event: number;
  event_predicted_central: number;
  lower_80: number;
  upper_80: number;
  lower_95: number;
  upper_95: number;
  actual_subsequent_close?: number | null;
  is_historical: boolean;
}

export interface FanChartData {
  base_date: string;
  base_price: number;
  daily_volatility_pct: number;
  pre_history: Array<{ trading_day: number; date: string; actual_close: number; is_historical: boolean }>;
  forecast_path: FanChartPoint[];
  has_actual_ground_truth: boolean;
}

export interface PredictionResult {
  event_family: string;
  event_subtype: string;
  target_symbol: string;
  prediction_date: string;
  calendar_alignment: {
    input_date: string;
    aligned_trading_date: string;
    alignment_type: string;
    lag_days: number;
  };
  forecast_horizon: string;
  predicted_direction: 'Positive' | 'Negative' | 'Neutral / Mixed';
  probability_up: number;
  probability_down: number;
  expected_return_pct: number;
  interval_lower_pct: number;
  interval_upper_pct: number;
  confidence_level: 'High' | 'Medium' | 'Low';
  horizons_breakdown: Record<string, { expected_car_pct: number; lower_bound_pct: number; upper_bound_pct: number }>;
  similar_events: AnalogueEvent[];
  main_drivers: Array<{ feature: string; value: number; contribution: number }>;
  sample_size: number;
  model_version: string;
  training_data_cutoff: string;
  explanation: string;
  limitations: string[];
  fan_chart?: FanChartData;
}

export interface BacktestResult {
  run_id: string;
  parameters: {
    start_date: string;
    end_date: string;
    cutoff_date: string;
    aligned_cutoff_date: string;
    event_family: string;
    target_symbol: string;
    horizon_days: number;
    simulated_event: {
      event_id: string;
      title: string;
      subtype: string;
      event_date: string;
    };
  };
  cutoff_price: number;
  prediction: PredictionResult;
  fan_chart: FanChartData;
  evaluation: {
    actual_end_price: number | null;
    actual_return_pct: number | null;
    predicted_return_pct: number;
    direction_correct: boolean | null;
    return_error_pct: number | null;
    interval_coverage_pct: number | null;
    observed_sessions: number;
  };
  data_isolation_audit: {
    max_training_date_used: string;
    strictly_no_future_prices: boolean;
    future_events_excluded: number;
  };
}

export interface NewsArticleItem {
  news_id: string;
  headline: string;
  summary: string;
  source_name: string;
  source_url: string;
  source_domain: string;
  source_tier: number;
  published_at: string | null;
  retrieved_at: string | null;
  event_family: string;
  event_subtype: string;
  relevance_score: number;
  verification_status: string;
}

export interface VerificationEvidence {
  source_name: string;
  source_url: string;
  source_tier: number;
  headline: string;
  published_at: string;
  similarity_score: number;
  evidence_type: string;
}

export interface VerificationResponse {
  verdict: 'Confirmed by credible reporting' | 'Partially corroborated' | 'Unverified' | 'Contradicted by verified evidence';
  heuristic_evidence_score: number;
  claim_summary: string;
  detected_event_family: string;
  detected_event_subtype: string;
  entities_detected: string[];
  institutions_detected: string[];
  fetch_notice: string | null;
  matched_evidence: VerificationEvidence[];
  explanation: string;
  scenarios: {
    scenario_a_true: {
      label: string;
      expected_return_pct: number;
      interval_lower_pct: number;
      interval_upper_pct: number;
      predicted_direction: string;
      forecast_points: FanChartPoint[];
    };
    scenario_b_false: {
      label: string;
      expected_return_pct: number;
      interval_lower_pct: number;
      interval_upper_pct: number;
      predicted_direction: string;
      forecast_points: Array<{ trading_day: number; date: string; projected_close: number; lower_95: number; upper_95: number }>;
      scientific_notice: string;
    };
  } | null;
}

export interface LiveMarketStatus {
  market_status: string;
  is_open: boolean;
  timestamp: string;
  provider: string;
  is_demo: boolean;
  is_stale: boolean;
}

export interface LiveIndices {
  timestamp: string;
  provider: string;
  is_demo: boolean;
  is_stale: boolean;
  aspi: {
    symbol: string;
    name: string;
    value: number;
    change: number;
    change_pct: number;
    high?: number;
    low?: number;
  };
  sp_sl20: {
    symbol: string;
    name: string;
    value: number;
    change: number;
    change_pct: number;
  };
}

export interface ListedSecurity {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
}
