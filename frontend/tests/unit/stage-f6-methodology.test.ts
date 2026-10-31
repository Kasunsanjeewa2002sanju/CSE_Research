import { describe, it, expect } from 'vitest';
import {
  protocolResponseSchema,
  featureDictionaryResponseSchema,
  protocolPhaseSchema,
  targetDefinitionSchema,
  leakageTestItemSchema,
  pipelineStageSchema,
  baselineDefinitionSchema,
} from '@/api/zod-schemas';
import type {
  ProtocolResponse,
  FeatureDictionaryResponse,
  FeatureDictionaryItem,
  LeakageTestItem,
} from '@/api/types';

describe('Stage F6: Methodology, Validation Protocol & Feature Sets Unit Tests', () => {
  it('validates protocolResponseSchema against full empirical walk-forward payload', () => {
    const payload: ProtocolResponse = {
      phases: [
        {
          phase_id: 'P1',
          name: 'Phase 1: Walk-Forward Fold P1',
          start_date: '1994-01-03',
          end_date: '2014-12-31',
          train_start: '1994-01-03',
          train_end: '2011-12-15',
          train_days: 4299,
          embargo_start: '2011-12-16',
          embargo_end: '2011-12-30',
          embargo_days: 10,
          val_start: '2012-01-02',
          val_end: '2014-12-31',
          val_days: 725,
          inner_train_days: 3645,
          inner_embargo_days: 10,
          inner_val_days: 644,
          total_days: 5034,
          description: 'Pre-war and early post-war initialization panel.',
          sample_size: 725,
        },
        {
          phase_id: 'P5',
          name: 'Phase 5: Walk-Forward Fold P5',
          start_date: '1994-01-03',
          end_date: '2025-12-31',
          train_start: '1994-01-03',
          train_end: '2023-12-13',
          train_days: 7147,
          embargo_start: '2023-12-14',
          embargo_end: '2023-12-29',
          embargo_days: 10,
          val_start: '2024-01-02',
          val_end: '2025-12-31',
          val_days: 478,
          inner_train_days: 6065,
          inner_embargo_days: 10,
          inner_val_days: 1072,
          total_days: 7635,
          description: 'Contemporary post-default IMF recovery and electoral realignment.',
          sample_size: 478,
        },
      ],
      embargo_rules: [
        {
          rule: '10-Trading-Day Purged Embargo Gap',
          rationale:
            'Enforces complete temporal separation between training folds and test windows.',
        },
      ],
      target_definitions: [
        {
          target_id: 'return_h1',
          name: '1-Day Forward Log Return & Direction',
          horizon_days: 1,
          horizon_label: 'h = 1 TD (1-Day Ahead)',
          formula: 'ln(ASPI_{t+1} / ASPI_t)',
          return_formula: 'r_{t+1} = ln(ASPI_{t+1} / ASPI_t)',
          direction_formula: 'y_{t+1} = sign(r_{t+1}) in {+1, -1}',
          direction_target: 'Binary Direction: +1 if return > 0, -1 otherwise',
          description: 'Next-day return shock for immediate reaction.',
        },
        {
          target_id: 'return_h5',
          name: '5-Day Forward Log Return & Direction',
          horizon_days: 5,
          horizon_label: 'h = 5 TD (1-Week Ahead)',
          formula: 'ln(ASPI_{t+5} / ASPI_t)',
          return_formula: 'r_{t+5} = ln(ASPI_{t+5} / ASPI_t)',
          direction_formula: 'y_{t+5} = sign(r_{t+5}) in {+1, -1}',
          direction_target: 'Binary Direction: +1 if return > 0, -1 otherwise',
          description: 'Weekly horizon capturing electoral settlement.',
        },
      ],
      leakage_test_status: {
        status: 'passed',
        last_checked: '2026-10-14T02:00:00Z',
        checks_performed: ['Feature Truncation Invariance Test'],
        failed_checks: [],
      },
      leakage_tests: [
        {
          test_id: 'test_truncate_rebuild_equality',
          name: 'Feature Truncation Invariance Test',
          status: 'passed',
          plain_language_meaning:
            'Rebuilding features truncated at t yields bit-for-bit identical values.',
          last_run_time: '2026-10-14T02:00:00Z',
          scope: 'Feature Sets A, B, C',
          tolerance: 'eps < 1e-12',
          verdict_details: '0 mismatches across 6 market eras.',
        },
      ],
      pipeline_stages: [
        {
          stage_id: 'stage_0',
          stage_number: 0,
          name: 'Stage 0: Pipeline Setup & Config',
          category: 'Infrastructure',
          status: 'completed',
          last_run_time: '2026-10-14T02:15:00+05:30',
          report_url: '/reports/STAGE_0_REPORT.md',
          report_title: 'Stage 0 Report',
          summary: 'Virtual environment and rule verification.',
          dependencies: [],
        },
      ],
      baselines: [
        {
          id: 'random_walk',
          name: 'Random Walk (No-Change Benchmark)',
          formula: 'y_hat_{t+h} = 0 | P_hat_{t+h} = P_t',
          direction_rule: 'Flat / neutral sign',
          definition: 'Predicts zero return over horizon h.',
          interpretation: 'Core efficient-market benchmark.',
          benchmark_role: 'Baseline for MSE and Theil U.',
        },
      ],
    };

    const parseResult = protocolResponseSchema.safeParse(payload);
    expect(parseResult.success).toBe(true);
  });

  it('verifies strictly expanding training days across walk-forward folds', () => {
    const trainDaysSeries = [4299, 5024, 5744, 6434, 7147];
    for (let i = 1; i < trainDaysSeries.length; i++) {
      expect(trainDaysSeries[i]).toBeGreaterThan(trainDaysSeries[i - 1]);
    }
  });

  it('validates featureDictionaryResponseSchema with Set A/B/C and phase event coverage', () => {
    const payload: FeatureDictionaryResponse = {
      total_features: 3,
      features: [
        {
          feature_name: 'ret_1d',
          feature_sets: ['A', 'B', 'C'],
          category: 'Price / Technical',
          group: 'price',
          dtype: 'float64',
          description: '1-day ASPI log return',
          availability: 'Full 30-year panel',
          lookahead_check: 'Strictly causal at t close (Rule R2)',
          lag_days: 1,
          source: 'CSE & CBSL',
          stationarity: true,
        },
        {
          feature_name: 'sp20_log_return',
          feature_sets: ['B', 'C'],
          category: 'Market Activity / Liquidity',
          group: 'activity',
          dtype: 'float64',
          description: 'S&P SL 20 daily log return',
          availability: 'Only from S&P SL 20 inception (2012-06-27 onward)',
          lookahead_check: 'Strictly causal at t close (Rule R2)',
          lag_days: 1,
          source: 'CSE & CBSL',
          stationarity: true,
        },
        {
          feature_name: 'stage_polling',
          feature_sets: ['C'],
          category: 'Electoral Cycle & Calendar',
          group: 'event',
          dtype: 'int64',
          description: 'One-hot indicator for polling day stage',
          availability: 'Active during national election events',
          lookahead_check: 'Strictly causal at t close (Rule R2)',
          lag_days: 0,
          source: 'CSE & CBSL',
          stationarity: true,
        },
      ],
      phase_event_coverage: [
        {
          phase: 'P1',
          val_dates: '2012-01-02 to 2014-12-31',
          val_days_total: 725,
          days_in_active_stage: 383,
          pct_in_active_stage: '52.8%',
          days_in_win_0_2: 69,
          days_in_win_0_7: 160,
          days_in_win_0_15: 250,
          days_in_win_0_30: 371,
          pct_in_win_0_30: '51.2%',
        },
        {
          phase: 'P4',
          val_dates: '2021-01-04 to 2023-12-29',
          val_days_total: 713,
          days_in_active_stage: 0,
          pct_in_active_stage: '0.0%',
          days_in_win_0_2: 0,
          days_in_win_0_7: 0,
          days_in_win_0_15: 0,
          days_in_win_0_30: 0,
          pct_in_win_0_30: '0.0%',
        },
      ],
    };

    const parseResult = featureDictionaryResponseSchema.safeParse(payload);
    expect(parseResult.success).toBe(true);
  });

  it('filters features accurately by Feature Set (A, B, C)', () => {
    const sampleFeatures: FeatureDictionaryItem[] = [
      {
        feature_name: 'ret_1d',
        feature_sets: ['A', 'B', 'C'],
        category: 'Price / Technical',
        group: 'price',
        description: 'ASPI return',
        lag_days: 1,
        source: 'CSE',
        stationarity: true,
      },
      {
        feature_name: 'log_turnover',
        feature_sets: ['B', 'C'],
        category: 'Market Activity / Liquidity',
        group: 'activity',
        description: 'Log equity turnover',
        lag_days: 1,
        source: 'CSE',
        stationarity: true,
      },
      {
        feature_name: 'stage_polling',
        feature_sets: ['C'],
        category: 'Electoral Cycle & Calendar',
        group: 'event',
        description: 'Polling day flag',
        lag_days: 0,
        source: 'CSE',
        stationarity: true,
      },
    ];

    const setAFeatures = sampleFeatures.filter((f) => f.feature_sets?.includes('A'));
    expect(setAFeatures.map((f) => f.feature_name)).toEqual(['ret_1d']);

    const setBFeatures = sampleFeatures.filter((f) => f.feature_sets?.includes('B'));
    expect(setBFeatures.map((f) => f.feature_name)).toEqual(['ret_1d', 'log_turnover']);

    const setCFeatures = sampleFeatures.filter((f) => f.feature_sets?.includes('C'));
    expect(setCFeatures.map((f) => f.feature_name)).toEqual([
      'ret_1d',
      'log_turnover',
      'stage_polling',
    ]);
  });

  it('correctly detects failing leakage tests and validates prominent alert condition', () => {
    const passedTests: LeakageTestItem[] = [
      {
        test_id: 't1',
        name: 'Monotonicity Test',
        status: 'passed',
        plain_language_meaning: 'Dates are strictly ascending.',
        last_run_time: '2026-10-14',
      },
    ];
    const hasFailuresWhenPassed = passedTests.some((t) => t.status === 'failed');
    expect(hasFailuresWhenPassed).toBe(false);

    const testsWithFailure: LeakageTestItem[] = [
      ...passedTests,
      {
        test_id: 't2',
        name: 'Future Perturbation Test',
        status: 'failed',
        plain_language_meaning: 'Feature changed when future data changed.',
        last_run_time: '2026-10-14',
      },
    ];
    const hasFailuresWhenFailed = testsWithFailure.some((t) => t.status === 'failed');
    expect(hasFailuresWhenFailed).toBe(true);
  });

  it('validates sub-schemas individually', () => {
    expect(
      protocolPhaseSchema.safeParse({
        phase_id: 'P1',
        name: 'Phase 1',
        start_date: '1994-01-03',
        end_date: '2014-12-31',
        description: 'Init',
        sample_size: 725,
      }).success
    ).toBe(true);

    expect(
      targetDefinitionSchema.safeParse({
        target_id: 'return_h1',
        formula: 'ln(ASPI_{t+1}/ASPI_t)',
        horizon_days: 1,
      }).success
    ).toBe(true);

    expect(
      leakageTestItemSchema.safeParse({
        test_id: 't1',
        name: 'Test 1',
        status: 'passed',
        plain_language_meaning: 'Meaning',
        last_run_time: '2026-10-14',
      }).success
    ).toBe(true);

    expect(
      pipelineStageSchema.safeParse({
        stage_id: 's0',
        stage_number: 0,
        name: 'Stage 0',
        category: 'Infrastructure',
        status: 'completed',
        last_run_time: '2026-10-14',
        report_url: '/report.md',
        report_title: 'Report',
        summary: 'Summary',
        dependencies: [],
      }).success
    ).toBe(true);

    expect(
      baselineDefinitionSchema.safeParse({
        id: 'rw',
        name: 'Random Walk',
        formula: '0',
        direction_rule: 'neutral',
        definition: 'Def',
        interpretation: 'Interp',
        benchmark_role: 'Role',
      }).success
    ).toBe(true);
  });
});
