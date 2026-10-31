import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { queryKeys } from '@/api/query-keys';
import {
  scenarioSubmitRequestSchema,
  scenarioSubmitResponseSchema,
  scenarioBacktestsResponseSchema,
  scenarioEvidenceSchema,
} from '@/api/zod-schemas';
import type {
  ScenarioSubmitResponse,
  ScenarioBacktestsResponse,
} from '@/api/types';
import { ScenarioInputPanel } from '@/features/scenario/components/ScenarioInputPanel';
import { ScenarioResultSummaryBand } from '@/features/scenario/components/ScenarioResultSummaryBand';
import { ScenarioThreePanels } from '@/features/scenario/components/ScenarioThreePanels';
import { ScenarioComparisonMatrix } from '@/features/scenario/components/ScenarioComparisonMatrix';
import { ScenarioEvidenceBlock } from '@/features/scenario/components/ScenarioEvidenceBlock';
import { ScenarioExplanationAndBacktests } from '@/features/scenario/components/ScenarioExplanationAndBacktests';
import { ScenarioUtilitiesBar } from '@/features/scenario/components/ScenarioUtilitiesBar';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

describe('Stage F9: Scenario Predictor Comprehensive Unit Tests', () => {
  const mockScenarioResponse: ScenarioSubmitResponse = {
    scenario_id: 'scen_test_20261018_001',
    status: 'completed',
    headline: 'Central Bank of Sri Lanka Cuts Policy Rates by 50bps',
    description: 'Monetary Board reduces SDFR and SLFR by 50 basis points.',
    publication_date: '2026-10-18',
    as_of_date: '2025-12-31',
    current_aspi: 22624.31,
    is_stale: false,
    stale_warning: null,
    meaning_of_false: 'the event does not occur',
    disclaimer: 'This scenario analysis represents statistical conditional expectations based on historical event studies and conformal counterfactual simulations. It does not constitute financial advice.',
    category: 'monetary_policy',
    category_label: 'Monetary Policy',
    stage: 'announcement',
    stage_label: 'Announcement',
    expected_direction: 'positive',
    expected_direction_arrow: '▲',
    expected_direction_sign: '+',
    evidence_strength: 'strong',
    evidence_strength_text: 'Statistically significant abnormal returns observed across 42 historical events (p < 0.01).',
    is_material_impact: true,
    material_impact_summary: 'Projected net divergence between scenarios is +3.80% at h=5.',
    scenarios: {
      CURRENT: {
        name: 'Current Baseline',
        description: 'Status quo trajectory without shock',
        primary_horizon: 5,
        expected_return: 0.0022,
        expected_return_pct: 0.22,
        target_aspi: 22674.08,
        probability_up: 53.5,
        trend_direction: 'neutral',
        trend_arrow: '▶',
        trend_sign: '',
        interval_80: [22480.0, 22860.0],
        interval_95: [22380.0, 22960.0],
        horizons: {
          '1': {
            horizon_days: 1,
            expected_return: 0.0005,
            expected_return_pct: 0.05,
            target_aspi: 22635.62,
            probability_up: 51.2,
            trend_direction: 'neutral',
            trend_arrow: '▶',
            trend_sign: '',
            interval_80: [22550.0, 22720.0],
            interval_95: [22490.0, 22780.0],
          },
          '2': {
            horizon_days: 2,
            expected_return: 0.001,
            expected_return_pct: 0.1,
            target_aspi: 22646.93,
            probability_up: 52.0,
            trend_direction: 'neutral',
            trend_arrow: '▶',
            trend_sign: '',
            interval_80: [22520.0, 22770.0],
            interval_95: [22440.0, 22850.0],
          },
          '5': {
            horizon_days: 5,
            expected_return: 0.0022,
            expected_return_pct: 0.22,
            target_aspi: 22674.08,
            probability_up: 53.5,
            trend_direction: 'neutral',
            trend_arrow: '▶',
            trend_sign: '',
            interval_80: [22480.0, 22860.0],
            interval_95: [22380.0, 22960.0],
          },
          '10': {
            horizon_days: 10,
            expected_return: 0.0045,
            expected_return_pct: 0.45,
            target_aspi: 22726.12,
            probability_up: 55.0,
            trend_direction: 'neutral',
            trend_arrow: '▶',
            trend_sign: '',
            interval_80: [22420.0, 23020.0],
            interval_95: [22290.0, 23150.0],
          },
        },
        sparkline: [22624.31, 22635.62, 22646.93, 22674.08, 22726.12],
      },
      TRUE: {
        name: 'If News is TRUE',
        description: 'Event occurs as reported',
        primary_horizon: 5,
        expected_return: 0.0215,
        expected_return_pct: 2.15,
        target_aspi: 23110.73,
        probability_up: 85.6,
        trend_direction: 'bullish',
        trend_arrow: '▲',
        trend_sign: '+',
        interval_80: [22850.0, 23370.0],
        interval_95: [22700.0, 23520.0],
        horizons: {
          '1': {
            horizon_days: 1,
            expected_return: 0.0085,
            expected_return_pct: 0.85,
            target_aspi: 22816.62,
            probability_up: 78.4,
            trend_direction: 'bullish',
            trend_arrow: '▲',
            trend_sign: '+',
            interval_80: [22680.0, 22950.0],
            interval_95: [22600.0, 23030.0],
          },
          '2': {
            horizon_days: 2,
            expected_return: 0.0142,
            expected_return_pct: 1.42,
            target_aspi: 22945.58,
            probability_up: 82.1,
            trend_direction: 'bullish',
            trend_arrow: '▲',
            trend_sign: '+',
            interval_80: [22750.0, 23140.0],
            interval_95: [22650.0, 23250.0],
          },
          '5': {
            horizon_days: 5,
            expected_return: 0.0215,
            expected_return_pct: 2.15,
            target_aspi: 23110.73,
            probability_up: 85.6,
            trend_direction: 'bullish',
            trend_arrow: '▲',
            trend_sign: '+',
            interval_80: [22850.0, 23370.0],
            interval_95: [22700.0, 23520.0],
          },
          '10': {
            horizon_days: 10,
            expected_return: 0.031,
            expected_return_pct: 3.1,
            target_aspi: 23325.66,
            probability_up: 88.0,
            trend_direction: 'bullish',
            trend_arrow: '▲',
            trend_sign: '+',
            interval_80: [22980.0, 23670.0],
            interval_95: [22810.0, 23840.0],
          },
        },
        sparkline: [22624.31, 22816.62, 22945.58, 23110.73, 23325.66],
      },
      FALSE: {
        name: 'If News is FALSE',
        description: 'The event does not occur',
        primary_horizon: 5,
        expected_return: -0.0165,
        expected_return_pct: -1.65,
        target_aspi: 22250.91,
        probability_up: 21.0,
        trend_direction: 'bearish',
        trend_arrow: '▼',
        trend_sign: '-',
        interval_80: [22020.0, 22480.0],
        interval_95: [21890.0, 22610.0],
        horizons: {
          '1': {
            horizon_days: 1,
            expected_return: -0.0042,
            expected_return_pct: -0.42,
            target_aspi: 22529.29,
            probability_up: 34.2,
            trend_direction: 'bearish',
            trend_arrow: '▼',
            trend_sign: '-',
            interval_80: [22410.0, 22650.0],
            interval_95: [22340.0, 22720.0],
          },
          '2': {
            horizon_days: 2,
            expected_return: -0.0088,
            expected_return_pct: -0.88,
            target_aspi: 22425.22,
            probability_up: 28.5,
            trend_direction: 'bearish',
            trend_arrow: '▼',
            trend_sign: '-',
            interval_80: [22270.0, 22580.0],
            interval_95: [22180.0, 22670.0],
          },
          '5': {
            horizon_days: 5,
            expected_return: -0.0165,
            expected_return_pct: -1.65,
            target_aspi: 22250.91,
            probability_up: 21.0,
            trend_direction: 'bearish',
            trend_arrow: '▼',
            trend_sign: '-',
            interval_80: [22020.0, 22480.0],
            interval_95: [21890.0, 22610.0],
          },
          '10': {
            horizon_days: 10,
            expected_return: -0.024,
            expected_return_pct: -2.4,
            target_aspi: 22081.33,
            probability_up: 16.5,
            trend_direction: 'bearish',
            trend_arrow: '▼',
            trend_sign: '-',
            interval_80: [21780.0, 22380.0],
            interval_95: [21600.0, 22560.0],
          },
        },
        sparkline: [22624.31, 22529.29, 22425.22, 22250.91, 22081.33],
      },
    },
    comparison_matrix: {
      columns: [
        { key: 'metric', label: 'Metric' },
        { key: 'current', label: 'Current Baseline' },
        { key: 'true_val', label: 'If News is TRUE' },
        { key: 'false_val', label: 'If News is FALSE' },
        { key: 'net_diff', label: 'Net Divergence' },
      ],
      rows: [
        {
          metric: 'Expected Return (h=5)',
          current: '+0.22%',
          true_val: '+2.15%',
          false_val: '-1.65%',
          net_diff: '+3.80%',
        },
        {
          metric: 'Target ASPI (h=5)',
          current: '22,674.08',
          true_val: '23,110.73',
          false_val: '22,250.91',
          net_diff: '+859.82 pts',
        },
        {
          metric: 'Probability Up (h=5)',
          current: '53.5%',
          true_val: '85.6%',
          false_val: '21.0%',
          net_diff: '+64.6%',
        },
        {
          metric: 'Evidence Strength',
          current: 'Neutral',
          true_val: 'Strong (n=42)',
          false_val: 'Counterfactual Model',
          net_diff: 'Calibrated',
        },
      ],
    },
    historical_evidence: {
      has_historical_match: true,
      matching_type: 'category_stage',
      matching_stage: 'announcement',
      window: '[-10, +10]',
      n_events: 42,
      mean_car: 0.0184,
      median_car: 0.0162,
      t_statistic: 3.42,
      t_pvalue: 0.0012,
      sign_test_pvalue: 0.0031,
      permutation_pvalue: 0.002,
      evidence_strength: 'strong',
      evidence_strength_text: 'Statistically significant abnormal returns observed across 42 historical events (p < 0.01).',
      car_series: [
        { day: -10, caar: -0.0005, ci_lower_95: -0.004, ci_upper_95: 0.003 },
        { day: 0, caar: 0.0075, ci_lower_95: 0.0035, ci_upper_95: 0.0115 },
        { day: 5, caar: 0.0184, ci_lower_95: 0.0125, ci_upper_95: 0.0243 },
        { day: 10, caar: 0.0215, ci_lower_95: 0.0145, ci_upper_95: 0.0285 },
      ],
    },
    explanation: 'Monetary policy rate cuts historically exert an immediate positive cumulative abnormal return on the Colombo ASPI.',
  };

  const mockBacktests: ScenarioBacktestsResponse = {
    summary: {
      total_tests: 20,
      hits: 15,
      misses: 5,
      hit_rate_pct: 75.0,
      coverage_80_pct: 40.0,
      coverage_95_pct: 85.0,
      mean_absolute_error_pct: 1.84,
    },
    backtests: [
      {
        scenario_name: 'CBSL cuts policy rates by 50 bps',
        date: '2024-03-26',
        target_date: '2024-04-02',
        horizon_h: 5,
        aspi_baseline: 11250.0,
        predicted_aspi: 11413.1,
        actual_aspi: 11454.7,
        predicted_impact_pct: 1.45,
        actual_impact_pct: 1.82,
        error_pct: 0.37,
        hit_direction: true,
        status: 'HIT',
        inside_ci_80: true,
        inside_ci_95: true,
      },
      {
        scenario_name: 'CBSL cuts SDFR and SLFR by 25 bps',
        date: '2024-07-24',
        target_date: '2024-07-31',
        horizon_h: 5,
        aspi_baseline: 11980.0,
        predicted_aspi: 12093.8,
        actual_aspi: 11929.7,
        predicted_impact_pct: 0.95,
        actual_impact_pct: -0.42,
        error_pct: 1.37,
        hit_direction: false,
        status: 'MISS',
        inside_ci_80: false,
        inside_ci_95: true,
      },
    ],
  };

  describe('1. Zod Schema Verification & Discipline Rules', () => {
    it('validates a valid ScenarioSubmitRequest', () => {
      const validReq = {
        headline: 'Test Headline about macroeconomic reform in Sri Lanka',
        description: 'Detailed description of fiscal consolidation reform',
        publication_date: '2026-10-18',
        category: 'fiscal_policy',
        sector: 'Diversified Financials',
        current_aspi: 22624.31,
      };
      const parsed = scenarioSubmitRequestSchema.safeParse(validReq);
      expect(parsed.success).toBe(true);
    });

    it('rejects invalid request with missing headline or invalid date', () => {
      const invalidReq = {
        headline: '',
        publication_date: 'not-a-date',
      };
      const parsed = scenarioSubmitRequestSchema.safeParse(invalidReq);
      expect(parsed.success).toBe(false);
    });

    it('validates ScenarioSubmitResponse and enforces strictly that FALSE means "the event does not occur"', () => {
      const parsed = scenarioSubmitResponseSchema.safeParse(mockScenarioResponse);
      expect(parsed.success).toBe(true);
      if (parsed.success) {
        expect(parsed.data.meaning_of_false).toBe('the event does not occur');
        expect(parsed.data.scenarios.TRUE).toBeDefined();
        expect(parsed.data.scenarios.FALSE).toBeDefined();
      }
    });

    it('validates ScenarioBacktestsResponse structure with hits and misses', () => {
      const parsed = scenarioBacktestsResponseSchema.safeParse(mockBacktests);
      expect(parsed.success).toBe(true);
      if (parsed.success) {
        expect(parsed.data.summary?.hits).toBe(15);
        expect(parsed.data.summary?.misses).toBe(5);
        expect(parsed.data.backtests.length).toBe(2);
        expect(parsed.data.backtests[0].hit_direction).toBe(true);
        expect(parsed.data.backtests[1].hit_direction).toBe(false);
      }
    });

    it('validates ScenarioEvidence structure with p-values and sample size n', () => {
      const parsed = scenarioEvidenceSchema.safeParse(mockScenarioResponse.historical_evidence);
      expect(parsed.success).toBe(true);
      if (parsed.success) {
        expect(parsed.data.n_events).toBe(42);
        expect(parsed.data.t_statistic).toBe(3.42);
        expect(parsed.data.t_pvalue).toBeLessThan(0.05);
      }
    });
  });

  describe('2. ScenarioInputPanel Component', () => {
    it('renders input elements, latest ASPI value, and Colombo date default', () => {
      const onSubmit = vi.fn();
      render(
        <ScenarioInputPanel
          onSubmit={onSubmit}
          isLoading={false}
          latestAspiValue={22624.31}
          latestAspiDate="2025-12-31"
          categories={[
            { id: 'monetary_policy', name: 'Monetary Policy' },
            { id: 'fiscal_policy', name: 'Fiscal Policy' },
          ]}
        />
      );

      // Latest ASPI badge
      expect(screen.getByText('22,624.31')).toBeInTheDocument();
      // Form fields
      expect(screen.getByLabelText(/Headline or Policy Declaration/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Context or Policy Description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Publication Date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Macro Category/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Target Sector/i)).toBeInTheDocument();
      // Submit button
      expect(screen.getByRole('button', { name: /Simulate Counterfactual Scenarios/i })).toBeInTheDocument();
    });

    it('shows validation errors when submitting an empty headline', () => {
      const onSubmit = vi.fn();
      render(
        <ScenarioInputPanel
          onSubmit={onSubmit}
          isLoading={false}
          latestAspiValue={22624.31}
          latestAspiDate="2025-12-31"
          categories={[{ id: 'monetary_policy', name: 'Monetary Policy' }]}
        />
      );

      const submitBtn = screen.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
      fireEvent.click(submitBtn);

      expect(screen.getByText(/Please enter a scenario headline or news title/i)).toBeInTheDocument();
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('shows validation error when headline is shorter than 5 characters', () => {
      const onSubmit = vi.fn();
      render(
        <ScenarioInputPanel
          onSubmit={onSubmit}
          isLoading={false}
          latestAspiValue={22624.31}
          latestAspiDate="2025-12-31"
          categories={[{ id: 'monetary_policy', name: 'Monetary Policy' }]}
        />
      );

      const input = screen.getByLabelText(/Headline or Policy Declaration/i);
      fireEvent.change(input, { target: { value: 'cbsl' } });

      const submitBtn = screen.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
      fireEvent.click(submitBtn);

      expect(screen.getByText(/Headline must be at least 5 characters/i)).toBeInTheDocument();
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('renders 3-phase stepper during loading state', () => {
      const onSubmit = vi.fn();
      render(
        <ScenarioInputPanel
          onSubmit={onSubmit}
          isLoading={true}
          latestAspiValue={22624.31}
          latestAspiDate="2025-12-31"
          categories={[{ id: 'monetary_policy', name: 'Monetary Policy' }]}
        />
      );

      expect(screen.getByText(/Semantic NLP Encoding/i)).toBeInTheDocument();
      expect(screen.getByText(/Historical Evidence Match/i)).toBeInTheDocument();
      expect(screen.getByText(/Conformal Forecasting/i)).toBeInTheDocument();
    });

    it('resets form when clicking Reset Form', () => {
      const onSubmit = vi.fn();
      render(
        <ScenarioInputPanel
          onSubmit={onSubmit}
          isLoading={false}
          latestAspiValue={22624.31}
          latestAspiDate="2025-12-31"
          categories={[{ id: 'monetary_policy', name: 'Monetary Policy' }]}
        />
      );

      const headlineInput = screen.getByLabelText(/Headline or Policy Declaration/i) as HTMLInputElement;
      fireEvent.change(headlineInput, { target: { value: 'Temporary Headline' } });
      expect(headlineInput.value).toBe('Temporary Headline');

      const resetBtn = screen.getByRole('button', { name: /Reset Form/i });
      fireEvent.click(resetBtn);
      expect(headlineInput.value).toBe('');
    });
  });

  describe('3. ScenarioResultSummaryBand Component', () => {
    it('renders category, stage, direction with arrow/sign, and evidence strength', () => {
      render(<ScenarioResultSummaryBand result={mockScenarioResponse} />);

      expect(screen.getByText('Monetary Policy')).toBeInTheDocument();
      expect(screen.getByText(/Stage: Announcement/i)).toBeInTheDocument();
      expect(screen.getByText(/\+ positive/i)).toBeInTheDocument();
      expect(screen.getByText(/Evidence: strong/i)).toBeInTheDocument();
      expect(screen.getByText(/This scenario analysis represents statistical conditional expectations/i)).toBeInTheDocument();
    });

    it('displays irrelevant news banner when is_material_impact is false', () => {
      const irrelevantResult: ScenarioSubmitResponse = {
        ...mockScenarioResponse,
        is_material_impact: false,
        material_impact_summary: 'True and False scenarios exhibit negligible divergence (<0.10%).',
      };
      render(<ScenarioResultSummaryBand result={irrelevantResult} />);
      expect(screen.getByText(/No Material Impact Detected:/i)).toBeInTheDocument();
      expect(screen.getByText(/True and False scenarios exhibit negligible divergence/i)).toBeInTheDocument();
    });

    it('displays stale warning banner when is_stale is true', () => {
      const staleResult: ScenarioSubmitResponse = {
        ...mockScenarioResponse,
        is_stale: true,
        stale_warning: 'Market data is older than 24 business hours. Projections may diverge from active order books.',
      };
      render(<ScenarioResultSummaryBand result={staleResult} />);
      expect(screen.getByText(/Market Baseline Warning:/i)).toBeInTheDocument();
      expect(screen.getByText(/Market data is older than 24 business hours/i)).toBeInTheDocument();
    });
  });

  describe('4. ScenarioThreePanels Component', () => {
    it('renders Baseline, TRUE, and FALSE panels with required metrics', () => {
      render(<ScenarioThreePanels result={mockScenarioResponse} />);

      // Panel Headers
      expect(screen.getByText('Current Baseline')).toBeInTheDocument();
      expect(screen.getByText('If News is TRUE')).toBeInTheDocument();
      expect(screen.getByText('If News is FALSE')).toBeInTheDocument();

      // Definition for FALSE stating "the event does not occur"
      expect(screen.getAllByText(/the event does not occur/i).length).toBeGreaterThan(0);

      // Values for h=5 default
      expect(screen.getByText('+2.15%')).toBeInTheDocument();
      expect(screen.getByText('23,110.73')).toBeInTheDocument();
      expect(screen.getByText('-1.65%')).toBeInTheDocument();
      expect(screen.getByText('22,250.91')).toBeInTheDocument();

      // P(Up) probabilities
      expect(screen.getByText('85.6%')).toBeInTheDocument();
      expect(screen.getByText('21.0%')).toBeInTheDocument();
    });

    it('allows changing horizon tabs', () => {
      render(<ScenarioThreePanels result={mockScenarioResponse} />);

      const h10Btn = screen.getByRole('button', { name: /h = 10/i });
      fireEvent.click(h10Btn);

      // After switching to h=10, the values for h=10 should be displayed
      expect(screen.getByText('+3.10%')).toBeInTheDocument();
      expect(screen.getByText('23,325.66')).toBeInTheDocument();
      expect(screen.getByText('-2.40%')).toBeInTheDocument();
    });
  });

  describe('5. ScenarioComparisonMatrix Component', () => {
    it('renders comparison table rows and columns dynamically from API response', () => {
      render(<ScenarioComparisonMatrix result={mockScenarioResponse} />);

      expect(screen.getByText('Metric')).toBeInTheDocument();
      expect(screen.getByText('If News is TRUE')).toBeInTheDocument();
      expect(screen.getByText('If News is FALSE')).toBeInTheDocument();
      expect(screen.getByText('Expected Return (h=5)')).toBeInTheDocument();
      expect(screen.getByText('Strong (n=42)')).toBeInTheDocument();
      expect(screen.getByText('Counterfactual Model')).toBeInTheDocument();
    });
  });

  describe('6. ScenarioEvidenceBlock Component', () => {
    it('renders sample size n, mean CAAR, p-values, and evidence narrative', () => {
      render(<ScenarioEvidenceBlock result={mockScenarioResponse} />);

      expect(screen.getByText(/n = 42/i)).toBeInTheDocument();
      expect(screen.getByText('+1.84%')).toBeInTheDocument();
      expect(screen.getByText('3.42')).toBeInTheDocument();
      expect(screen.getByText(/p = 0\.0012/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Statistically significant abnormal returns observed across 42 historical/i)
      ).toBeInTheDocument();
    });

    it('toggles accessible CAR data table view', () => {
      render(<ScenarioEvidenceBlock result={mockScenarioResponse} />);

      const toggleBtn = screen.getByRole('button', { name: /Accessible Table/i });
      fireEvent.click(toggleBtn);

      expect(screen.getByText('Event Day')).toBeInTheDocument();
      expect(screen.getByText('CAAR (%)')).toBeInTheDocument();
    });
  });

  describe('7. ScenarioExplanationAndBacktests Component', () => {
    it('renders methodology explanation and switches to back-tests tab', () => {
      const queryClient = createTestQueryClient();
      queryClient.setQueryData(queryKeys.scenarios.backtests(), mockBacktests);

      render(
        <QueryClientProvider client={queryClient}>
          <ScenarioExplanationAndBacktests result={mockScenarioResponse} />
        </QueryClientProvider>
      );

      // Explanation view
      expect(screen.getByText(/Monetary policy rate cuts historically exert/i)).toBeInTheDocument();

      // Switch to Back-Tests tab
      const backtestsTab = screen.getByRole('button', { name: /Walk-Forward Back-Tests/i });
      fireEvent.click(backtestsTab);

      // Back-test summary metrics
      expect(screen.getByText('75.0%')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('1.84%')).toBeInTheDocument();
    });
  });

  describe('8. ScenarioUtilitiesBar Component', () => {
    it('renders export buttons, permalink copy, and session history drawer', () => {
      const mockHistory = [
        {
          id: 'scen_001',
          timestamp: '18:00:00',
          headline: 'CBSL cuts policy rates by 50bps',
          category: 'Monetary Policy',
          trueReturnPct: 2.15,
          falseReturnPct: -1.65,
          targetAspi: 23110.73,
          direction: 'positive',
          evidenceStrength: 'strong',
        },
      ];
      const onRestore = vi.fn();

      render(
        <BrowserRouter>
          <ScenarioUtilitiesBar
            result={mockScenarioResponse}
            sessionHistory={mockHistory}
            onRestoreRun={onRestore}
          />
        </BrowserRouter>
      );

      expect(screen.getByRole('button', { name: /Permalink/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Export JSON/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /PNG Chart/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Print \/ PDF/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Session Runs \(1\)/i })).toBeInTheDocument();

      // Open session history drawer
      const historyBtn = screen.getByRole('button', { name: /Session Runs \(1\)/i });
      fireEvent.click(historyBtn);

      expect(screen.getByText(/Session Simulation History/i)).toBeInTheDocument();
      expect(screen.getByText('CBSL cuts policy rates by 50bps')).toBeInTheDocument();
    });
  });
});
