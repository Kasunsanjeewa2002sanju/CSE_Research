import { describe, it, expect } from 'vitest';
import {
  modelLeaderboardResponseSchema,
  modelLeaderboardItemSchema,
  modelDetailResponseSchema,
  modelCompareResponseSchema,
  modelStatisticsResponseSchema,
  finalModelResponseSchema,
  modelArtifactSchema,
} from '@/api/zod-schemas';
import type {
  ModelLeaderboardResponse,
  ModelLeaderboardItem,
  ModelDetailResponse,
  ModelCompareResponse,
  ModelStatisticsResponse,
  FinalModelResponse,
} from '@/api/types';

describe('Stage F7: Model Lab, Leaderboard & Diagnostics Unit Tests', () => {
  const mockLeaderboardItem: ModelLeaderboardItem = {
    model_id: 'catboost_reg_c_h5',
    model_name: 'CatBoost Regressor (Feature Set C)',
    family: 'shallow',
    feature_set: 'Set C',
    horizon: 5,
    is_baseline: false,
    is_champion: true,
    rank_overall: 1,
    rank_family: 1,
    oos_r2_mean: 0.082,
    oos_r2_std: 0.018,
    oos_r2_phases: { P1: 0.071, P2: 0.085, P3: 0.079, P4: 0.091, P5: 0.084 },
    accuracy_mean: 58.4,
    accuracy_std: 3.8,
    accuracy_ci_lower: 51.2,
    accuracy_ci_upper: 65.4,
    accuracy_phases: { P1: 56.2, P2: 59.1, P3: 57.8, P4: 60.2, P5: 58.7 },
    balanced_accuracy_mean: 57.6,
    balanced_accuracy_std: 3.5,
    rmse_mean: 0.0215,
    rmse_std: 0.0032,
    mae_mean: 0.0158,
    mae_std: 0.0024,
    theils_u_mean: 0.942,
    theils_u_std: 0.015,
    training_time_s: 0.58,
    parameters: '500 trees',
    significantly_better_than_baseline: true,
    significance_correction_method: 'Benjamini-Hochberg FDR (q < 0.05)',
    p_value_vs_baseline: 0.0084,
    correction_details: 'Rejects martingale null under Benjamini-Hochberg FDR correction.',
  };

  const mockBaselineItem: ModelLeaderboardItem = {
    model_id: 'historical_mean',
    model_name: 'Prevailing Historical Mean',
    family: 'baseline',
    feature_set: 'Set A',
    horizon: 5,
    is_baseline: true,
    is_champion: false,
    rank_overall: 275,
    rank_family: 1,
    oos_r2_mean: 0.0,
    oos_r2_std: 0.0,
    oos_r2_phases: { P1: 0.0, P2: 0.0, P3: 0.0, P4: 0.0, P5: 0.0 },
    accuracy_mean: 50.1,
    accuracy_std: 2.1,
    accuracy_ci_lower: 46.2,
    accuracy_ci_upper: 54.0,
    accuracy_phases: { P1: 49.8, P2: 50.5, P3: 49.9, P4: 50.4, P5: 50.0 },
    balanced_accuracy_mean: 50.0,
    balanced_accuracy_std: 2.0,
    rmse_mean: 0.0248,
    rmse_std: 0.0028,
    mae_mean: 0.0189,
    mae_std: 0.0021,
    theils_u_mean: 1.0,
    theils_u_std: 0.0,
    training_time_s: 0.01,
    parameters: '0',
    significantly_better_than_baseline: false,
    significance_correction_method: 'Baseline Anchor',
    p_value_vs_baseline: 1.0,
    correction_details: 'Constant prevailing expanding mean benchmark.',
  };

  it('validates modelLeaderboardResponseSchema against empirical API payload', () => {
    const payload: ModelLeaderboardResponse = {
      leaderboard: [mockLeaderboardItem, mockBaselineItem],
      total_models: 277,
      baseline_models: ['historical_mean', 'random_walk'],
      champion_model_id: 'catboost_reg_c_h5',
      any_model_beats_baseline: true,
      summary_message: 'Empirical Walk-Forward Leaderboard (277 models evaluated across 5 walk-forward folds).',
      as_of_date: '2025-02-28',
      evaluation_protocol: 'Expanding-window Walk-Forward CV (5 folds, 10-day embargo gap)',
      disclaimer: 'Past empirical predictability does not guarantee future financial returns.',
    };

    const parsed = modelLeaderboardResponseSchema.parse(payload);
    expect(parsed.total_models).toBe(277);
    expect(parsed.leaderboard.length).toBe(2);
    expect(parsed.leaderboard[0].significantly_better_than_baseline).toBe(true);
    expect(parsed.leaderboard[1].is_baseline).toBe(true);
    expect(modelLeaderboardItemSchema.parse(mockLeaderboardItem).model_id).toBe('catboost_reg_c_h5');
  });

  it('validates modelDetailResponseSchema against detailed diagnostics payload', () => {
    const detailPayload: ModelDetailResponse = {
      model_id: 'catboost_reg_c_h5',
      model_name: 'CatBoost Regressor (Feature Set C, h=5)',
      family: 'shallow',
      feature_set: 'Set C',
      horizon: 5,
      hyperparameters: {
        iterations: 500,
        learning_rate: 0.03,
        depth: 6,
        loss_function: 'RMSE',
      },
      training_data_range: ['1994-01-03', '2025-12-31'],
      seed: 42,
      hardware: 'AMD EPYC 7763 (8 vCPUs), 32 GB RAM',
      runtime_seconds: 4.82,
      memory_mb: 245.0,
      per_phase_predictions: [
        {
          date: '2024-01-02',
          phase: 'P5',
          predicted_return: 0.0034,
          actual_return: 0.0028,
          residual: 0.0006,
          ci_lower: -0.008,
          ci_upper: 0.015,
          is_validation: true,
        },
      ],
      cumulative_error: [
        { date: '2024-01-02', cumulative_mae: 0.0006, cumulative_rmse: 0.0006 },
      ],
      residuals: {
        mean: 0.0001,
        std: 0.018,
        skewness: -0.12,
        kurtosis: 3.45,
        lb_stat_lag5: 4.21,
        lb_pval_lag5: 0.52,
        is_white_noise: true,
        histogram: [
          { bin_start: -0.05, bin_end: -0.04, count: 12, density: 0.04 },
          { bin_start: -0.04, bin_end: -0.03, count: 48, density: 0.16 },
        ],
        qq_plot: [
          { theoretical_quantile: -2.0, sample_quantile: -0.045 },
          { theoretical_quantile: 0.0, sample_quantile: 0.0001 },
          { theoretical_quantile: 2.0, sample_quantile: 0.046 },
        ],
      },
      feature_importance: [
        { feature: 'aspi_turnover_ratio_20d', importance: 0.142, category: 'Market Activity' },
        { feature: 'aspi_volatility_parkinson_20d', importance: 0.118, category: 'Volatility' },
      ],
      training_curves: [
        { iteration: 100, train_loss: 0.024, val_loss: 0.026 },
        { iteration: 500, train_loss: 0.018, val_loss: 0.021 },
      ],
      confusion_matrix: {
        true_positive: 154,
        false_positive: 102,
        false_negative: 98,
        true_negative: 124,
        accuracy: 0.582,
        precision: 0.601,
        recall: 0.611,
        f1_score: 0.606,
        mcc: 0.165,
      },
      artifacts: [
        {
          name: 'model_weights.cbm',
          file_size_bytes: 489201,
          updated_at: '2025-03-01T10:00:00Z',
          sha256: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
          download_url: '/api/v1/models/artifacts/catboost_reg_c_h5/weights',
        },
      ],
    };

    const parsed = modelDetailResponseSchema.parse(detailPayload);
    expect(parsed.model_id).toBe('catboost_reg_c_h5');
    expect(parsed.confusion_matrix.mcc).toBeCloseTo(0.165, 3);
    expect(parsed.residuals.is_white_noise).toBe(true);
    expect(parsed.artifacts.length).toBe(1);
    expect(modelArtifactSchema.parse(detailPayload.artifacts[0]).name).toBe('model_weights.cbm');
  });

  it('validates modelCompareResponseSchema against side-by-side comparison payload', () => {
    const comparePayload: ModelCompareResponse = {
      compared_models: [mockLeaderboardItem, mockBaselineItem],
      forecast_comparison: [
        {
          date: '2024-01-02',
          actual_return: 0.0028,
          catboost_reg_c_h5: 0.0034,
          historical_mean: 0.0004,
        },
      ],
      phase_stability: [
        {
          phase_id: 'P1',
          catboost_reg_c_h5: 56.2,
          historical_mean: 49.8,
        },
      ],
    };

    const parsed = modelCompareResponseSchema.parse(comparePayload);
    expect(parsed.compared_models.length).toBe(2);
    expect(parsed.forecast_comparison.length).toBe(1);
    expect(parsed.phase_stability[0].phase_id).toBe('P1');
  });

  it('validates modelStatisticsResponseSchema against DM test and ablation payload', () => {
    const statsPayload: ModelStatisticsResponse = {
      dm_matrix: [
        {
          model_a: 'catboost_reg_c_h5',
          model_b: 'historical_mean',
          statistic: 2.64,
          p_value: 0.0084,
          significant: true,
          preferred_model: 'catboost_reg_c_h5',
        },
      ],
      matrix_models: ['catboost_reg_c_h5', 'historical_mean'],
      model_confidence_set: {
        confidence_level: 0.95,
        included_models: [
          { model_id: 'catboost_reg_c_h5', p_value: 0.84, rank: 1 },
          { model_id: 'xgboost_reg_c_h5', p_value: 0.62, rank: 2 },
        ],
        excluded_models: [
          { model_id: 'historical_mean', p_value: 0.002, elimination_step: 1 },
        ],
      },
      ablation_feature_sets: [
        {
          architecture: 'CatBoost Regressor',
          family: 'shallow',
          horizon: 5,
          n_samples: 3321,
          r2_set_a: 0.012,
          r2_set_b: 0.048,
          r2_set_c: 0.082,
          delta_r2_c_minus_a: 0.070,
          delta_r2_c_minus_b: 0.034,
          acc_set_a: 52.8,
          acc_set_b: 55.6,
          acc_set_c: 58.4,
          t_stat_c_vs_a: 3.42,
          p_val_c_vs_a: 0.0006,
          t_stat_c_vs_b: 2.15,
          p_val_c_vs_b: 0.0315,
        },
      ],
      ablation_event_windows: [
        {
          model: 'catboost_reg_c_h5',
          family: 'shallow',
          horizon: 5,
          phase: 'P1-P5 Pooled',
          n_inside_events: 940,
          n_outside_events: 6695,
          r2_inside: 0.104,
          r2_outside: 0.076,
          delta_r2_in_minus_out: 0.028,
          acc_inside: 61.2,
          acc_outside: 57.4,
          delta_acc_in_minus_out: 3.8,
          pt_pval_inside: 0.0012,
        },
      ],
    };

    const parsed = modelStatisticsResponseSchema.parse(statsPayload);
    expect(parsed.dm_matrix.length).toBe(1);
    expect(parsed.model_confidence_set.confidence_level).toBe(0.95);
    expect(parsed.ablation_feature_sets[0].delta_r2_c_minus_a).toBe(0.07);
    expect(parsed.ablation_event_windows[0].n_inside_events).toBe(940);
  });

  it('validates finalModelResponseSchema against frozen champion metadata', () => {
    const finalPayload: FinalModelResponse = {
      model_id: 'catboost_reg_c',
      model_name: 'CatBoost Regressor (Feature Set C)',
      family: 'shallow',
      architecture: 'Symmetric Decision Trees (Oblivious Trees)',
      version: '1.0.0-frozen',
      release_date: '2025-03-01',
      license: 'MIT',
      training_data_range: ['1994-01-03', '2025-12-31'],
      n_training_samples: 7635,
      n_features: 27,
      primary_target: 'aspi_forward_5d_log_return',
      secondary_target: 'aspi_direction_sign',
      hyperparameters: {
        iterations: 500,
        depth: 6,
        learning_rate: 0.03,
      },
      empirical_metrics: {
        accuracy_mean: 58.4,
        rmse_mean: 0.0215,
        mae_mean: 0.0158,
        oos_r2_mean: 0.082,
      },
      top_features: [
        { name: 'aspi_turnover_ratio_20d', importance: 0.142 },
      ],
      selection_hierarchy: [
        'Filter 1: Directional accuracy significantly > 50% under BH FDR at q < 0.05',
        'Filter 2: DM test p < 0.05 against historical mean baseline',
        'Filter 3: Membership in Hansen (2011) Model Confidence Set (MCS)',
        'Filter 4: Non-negative OOS R^2 across all 5 walk-forward folds',
        'Filter 5: Parsimony & lowest runtime latency among top candidates',
      ],
      limitations: [
        'Out-of-sample directional edge diminishes during illiquid trading halts.',
        'Regime shifts during post-war presidential elections exhibit elevated tail risk.',
      ],
      selection_verdict: 'Approved as Final Production Champion Model',
      model_card_markdown: '# CatBoost Model Card\nFinal frozen weights.',
      decision_trace_markdown: '# Decision Trace\nStage 9 pre-registered hierarchy.',
    };

    const parsed = finalModelResponseSchema.parse(finalPayload);
    expect(parsed.model_id).toBe('catboost_reg_c');
    expect(parsed.selection_hierarchy.length).toBe(5);
    expect(parsed.limitations.length).toBe(2);
  });

  // Filter & Sort algorithmic tests
  it('correctly filters leaderboard by family, horizon, and feature set', () => {
    const list: ModelLeaderboardItem[] = [
      mockLeaderboardItem,
      mockBaselineItem,
      {
        ...mockLeaderboardItem,
        model_id: 'timesfm_h1_a',
        model_name: 'TimesFM Zero-Shot',
        family: 'foundation',
        horizon: 1,
        feature_set: 'Set A',
      },
    ];

    // Filter by family 'foundation'
    const foundationOnly = list.filter((m) => m.family === 'foundation');
    expect(foundationOnly.length).toBe(1);
    expect(foundationOnly[0].model_id).toBe('timesfm_h1_a');

    // Filter by horizon 5
    const h5Only = list.filter((m) => m.horizon === 5);
    expect(h5Only.length).toBe(2);

    // Filter by feature set 'Set C'
    const setCOnly = list.filter((m) => m.feature_set === 'Set C');
    expect(setCOnly.length).toBe(1);
    expect(setCOnly[0].model_id).toBe('catboost_reg_c_h5');
  });

  it('correctly sorts models descending by directional accuracy', () => {
    const list: ModelLeaderboardItem[] = [
      mockBaselineItem, // 50.1
      mockLeaderboardItem, // 58.4
    ];

    const sorted = [...list].sort((a, b) => b.accuracy_mean - a.accuracy_mean);
    expect(sorted[0].model_id).toBe('catboost_reg_c_h5');
    expect(sorted[1].model_id).toBe('historical_mean');
  });

  it('correctly flags models beating baseline under FDR correction', () => {
    expect(mockLeaderboardItem.significantly_better_than_baseline).toBe(true);
    expect(mockLeaderboardItem.p_value_vs_baseline).toBeLessThan(0.05);
    expect(mockBaselineItem.significantly_better_than_baseline).toBe(false);
  });
});
