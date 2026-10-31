import { describe, it, expect } from 'vitest';
import {
  eventStudyCaarResponseSchema,
  eventStudyHeatmapResponseSchema,
  eventStudyPerEventResponseSchema,
  eventStudySummaryResponseSchema,
} from '@/api/zod-schemas';
import {
  buildCaarTrajectoryOption,
  buildAbnormalReturnBarsOption,
  buildHeatmapOption,
  buildForestPlotOption,
  buildPermutationHistogramOption,
} from '@/features/event-study/utils/chart-options';
import type {
  EventStudyCaarResponse,
  EventStudyHeatmapResponse,
  EventStudyPerEventItem,
} from '@/features/event-study/types';

describe('Stage F5: Event Study Econometric Explorer Unit Tests', () => {
  it('validates eventStudyCaarResponseSchema against empirical payload', () => {
    const mockPayload: EventStudyCaarResponse = {
      window_days: '[-7,+7]',
      election_type: 'Presidential',
      stage: 'polling',
      event_count: 5,
      warn_small_sample: true,
      small_sample_warning_text: 'Small sample size (n < 10): statistical power limited',
      sample_size_threshold: 10,
      caar_stats: {
        caar: 2.45,
        median_car: 2.12,
        std_car: 3.45,
        t_stat: 1.45,
        t_pval: 0.18,
        t_pval_bh: 0.35,
        permutation_pval: 0.038,
        sign_test_pval: 0.0436,
        significance_badge: 'Marginal (p < 0.10)',
      },
      data: [
        {
          day: -2,
          caar: 0.5,
          ci_lower_95: -1.2,
          ci_upper_95: 2.2,
          ar: 0.2,
          ar_t_stat: 1.1,
          ar_p_val: 0.27,
          sample_size: 5,
        },
        {
          day: 0,
          caar: 1.8,
          ci_lower_95: 0.2,
          ci_upper_95: 3.4,
          ar: 1.3,
          ar_t_stat: 2.5,
          ar_p_val: 0.02,
          sample_size: 5,
        },
      ],
      individual_events: [
        {
          event_id: 'ELEC_23',
          name: '2024 Sri Lankan Presidential Election',
          year: 2024,
          election_type: 'Presidential',
          stage: 'polling',
          date: '2024-09-23',
          car: 2.45,
          path: [
            { day: -2, car: 0.5 },
            { day: 0, car: 1.8 },
          ],
        },
      ],
      permutation_distribution: {
        bins: [{ min: -1.0, max: -0.5, count: 120 }],
        observed_value: 2.45,
        p_value: 0.038,
        draws: 10000,
      },
      modelled_trajectory: null,
      p_value_permutation: 0.038,
      p_value_bonferroni: 0.076,
      statistical_significance: true,
      as_of_date: '2025-12-31',
    };

    const parsed = eventStudyCaarResponseSchema.parse(mockPayload);
    expect(parsed.window_days).toBe('[-7,+7]');
    expect(parsed.event_count).toBe(5);
    expect(parsed.data).toHaveLength(2);
    expect(parsed.caar_stats?.caar).toBe(2.45);
  });

  it('validates eventStudyHeatmapResponseSchema structure and cell integrity', () => {
    const mockHeatmap: EventStudyHeatmapResponse = {
      cells: [
        {
          election_type: 'Parliamentary',
          stage: 'polling',
          window: '[-7,+7]',
          caar: -1.48,
          median_car: 0.12,
          std_car: 10.76,
          t_stat: -0.89,
          t_pval: 0.3777,
          t_pval_bh: 0.8559,
          sign_test_pval: 0.8776,
          wilcoxon_pval_bh: 0.7169,
          n: 42,
          warn_small_sample: false,
          is_significant: false,
        },
      ],
      windows: ['[-7,+7]'],
      election_types: ['Parliamentary'],
      stages: ['polling'],
      total_cells: 1,
    };

    const parsed = eventStudyHeatmapResponseSchema.parse(mockHeatmap);
    expect(parsed.cells).toHaveLength(1);
    expect(parsed.cells[0].caar).toBe(-1.48);
    expect(parsed.cells[0].n).toBe(42);
  });

  it('validates eventStudyPerEventResponseSchema with confidence intervals and ASPI change', () => {
    const mockPerEvent = {
      items: [
        {
          event_id: 'ELEC_23',
          event_name: '2024 Sri Lankan Presidential Election',
          election_type: 'Presidential',
          stage: 'polling',
          date: '2024-09-23',
          raw_date: '2024-09-21',
          year: 2024,
          window: '[0,+7]',
          car: 8.36,
          bw_se: 2.15,
          ci_lower: 4.15,
          ci_upper: 12.57,
          t_stat: 3.89,
          p_value: 0.0042,
          permutation_p_val: 0.0558,
          corrected_p_val: 0.0845,
          is_overlapping: false,
          aspi_before: 10966.51,
          aspi_after: 11671.87,
          change_pct: 6.43,
          significance_badge: 'Significant (p < 0.05)',
        },
      ],
      total: 1,
      window: '[0,+7]',
    };

    const parsed = eventStudyPerEventResponseSchema.parse(mockPerEvent);
    expect(parsed.items).toHaveLength(1);
    expect(parsed.items[0].car).toBe(8.36);
    expect(parsed.items[0].change_pct).toBe(6.43);
  });

  it('validates eventStudySummaryResponseSchema containing methodology and caveats', () => {
    const mockSummary = {
      summary_markdown: '# Summary\nEmpirical event study findings.',
      methodology: 'Constant-Mean Return Model across 9 windows.',
      caveats: ['Historical association does not imply causation.'],
      small_sample_threshold: 10,
      disclaimer: 'Academic research only.',
    };

    const parsed = eventStudySummaryResponseSchema.parse(mockSummary);
    expect(parsed.caveats).toHaveLength(1);
    expect(parsed.small_sample_threshold).toBe(10);
  });

  it('buildCaarTrajectoryOption generates valid ECharts configuration with 95% band and mean line', () => {
    const points = [
      { day: -1, caar: 0.1, ci_lower_95: -0.8, ci_upper_95: 1.0, sample_size: 10 },
      { day: 0, caar: 0.9, ci_lower_95: -0.2, ci_upper_95: 2.0, sample_size: 10 },
      { day: 1, caar: 1.4, ci_lower_95: 0.1, ci_upper_95: 2.7, sample_size: 10 },
    ];

    const option = buildCaarTrajectoryOption(points, []);
    expect(option.grid).toBeDefined();
    expect(option.xAxis).toBeDefined();
    expect(option.yAxis).toBeDefined();
    expect(Array.isArray(option.series)).toBe(true);

    // Verify mean line exists with approved primary blue color #0A2A66
    const seriesList = option.series as Array<{ name?: string; lineStyle?: { color?: string } }>;
    const meanSeries = seriesList.find((s) => s.name === 'Mean CAAR Path');
    expect(meanSeries).toBeDefined();
    expect(meanSeries?.lineStyle?.color).toBe('#0A2A66');
  });

  it('buildAbnormalReturnBarsOption generates daily AR bars', () => {
    const points = [
      { day: -1, caar: 0.1, ci_lower_95: -0.8, ci_upper_95: 1.0, ar: 0.1, sample_size: 10 },
      { day: 0, caar: 0.9, ci_lower_95: -0.2, ci_upper_95: 2.0, ar: 0.8, sample_size: 10 },
    ];

    const option = buildAbnormalReturnBarsOption(points);
    expect(option.series).toBeDefined();
    const seriesList = option.series as Array<{ type?: string }>;
    expect(seriesList[0].type).toBe('bar');
  });

  it('buildHeatmapOption maps correct matrix and color range', () => {
    const mockHeatmap: EventStudyHeatmapResponse = {
      cells: [
        {
          election_type: 'Presidential',
          stage: 'polling',
          window: '[0,+7]',
          caar: 0.67,
          median_car: 0.74,
          std_car: 3.12,
          t_stat: 0.73,
          t_pval: 0.4696,
          t_pval_bh: 0.8559,
          sign_test_pval: 0.3616,
          n: 30,
          warn_small_sample: false,
          is_significant: false,
        },
      ],
      windows: ['[0,+7]'],
      election_types: ['Presidential'],
      stages: ['polling'],
      total_cells: 1,
    };

    const option = buildHeatmapOption(mockHeatmap);
    expect(option.visualMap).toBeDefined();
    expect(option.series).toBeDefined();
  });

  it('buildForestPlotOption creates scatter series with zero reference line', () => {
    const mockItems: EventStudyPerEventItem[] = [
      {
        event_id: 'ELEC_23',
        event_name: '2024 Sri Lankan Presidential Election',
        election_type: 'Presidential',
        stage: 'polling',
        date: '2024-09-23',
        year: 2024,
        window: '[0,+7]',
        car: 8.36,
        bw_se: 2.15,
        ci_lower: 4.15,
        ci_upper: 12.57,
        t_stat: 3.89,
        p_value: 0.0042,
        permutation_p_val: 0.0558,
        corrected_p_val: 0.0845,
        is_overlapping: false,
        aspi_before: 10966.51,
        aspi_after: 11671.87,
        change_pct: 6.43,
        significance_badge: 'Significant (p < 0.05)',
      },
    ];

    const option = buildForestPlotOption(mockItems);
    const seriesList = option.series as Array<{ type?: string; markLine?: unknown }>;
    const scatterSeries = seriesList.find((s) => s.type === 'scatter');
    expect(scatterSeries).toBeDefined();
    expect(scatterSeries?.markLine).toBeDefined();
  });

  it('buildPermutationHistogramOption sets observed CAAR markLine', () => {
    const dist = {
      bins: [
        { min: -1.0, max: -0.5, count: 500 },
        { min: -0.5, max: 0.0, count: 2500 },
        { min: 0.0, max: 0.5, count: 2600 },
      ],
      observed_value: 1.85,
      p_value: 0.038,
      draws: 10000,
    };

    const option = buildPermutationHistogramOption(dist);
    const seriesList = option.series as Array<{ markLine?: unknown }>;
    expect(seriesList[0].markLine).toBeDefined();
  });

  it('strict Rule FR1 verification: ensures no red or green categorical colors are used for election types', () => {
    const option = buildCaarTrajectoryOption([
      { day: 0, caar: 1.0, ci_lower_95: 0.0, ci_upper_95: 2.0, sample_size: 10 },
    ]);

    const jsonStr = JSON.stringify(option).toLowerCase();
    // Verify no plain red (#ff0000, red) or green (#00ff00, green) are used
    expect(jsonStr).not.toContain('#ff0000');
    expect(jsonStr).not.toContain('#00ff00');
    expect(jsonStr).not.toContain('"color":"red"');
    expect(jsonStr).not.toContain('"color":"green"');
  });
});
