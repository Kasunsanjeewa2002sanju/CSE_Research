import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { ContractError } from '@/components/ui/ContractError';
import { ScenarioInputPanel } from '../components/ScenarioInputPanel';
import { ScenarioResultSummaryBand } from '../components/ScenarioResultSummaryBand';
import { ScenarioThreePanels } from '../components/ScenarioThreePanels';
import { ScenarioCombinedChart } from '../components/ScenarioCombinedChart';
import { ScenarioComparisonMatrix } from '../components/ScenarioComparisonMatrix';
import { ScenarioEvidenceBlock } from '../components/ScenarioEvidenceBlock';
import { ScenarioExplanationAndBacktests } from '../components/ScenarioExplanationAndBacktests';
import { ScenarioUtilitiesBar } from '../components/ScenarioUtilitiesBar';
import { useScenarioSubmitMutation } from '../hooks/useScenarioData';
import { useLiveMarket } from '@/stores/market-store';
import { useMarketStatsQuery } from '@/features/overview/hooks/useOverviewData';
import type {
  ScenarioSubmitRequest,
  ScenarioSubmitResponse,
  ScenarioRunRecord,
} from '../types';

export default function ScenarioPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const newsIdParam = searchParams.get('news');
  const headlineParam = searchParams.get('headline');
  const dateParam = searchParams.get('date');
  const categoryParam = searchParams.get('category');
  const sectorParam = searchParams.get('sector');

  // Synchronize baseline ASPI with the Overview page ASPI index stat card
  const liveAspi = useLiveMarket((s) => s.snapshot?.aspi_value);
  const liveDate = useLiveMarket((s) => s.snapshot?.source_timestamp);
  const { data: stats } = useMarketStatsQuery();

  const currentBaselineAspi = liveAspi ?? stats?.baseline_aspi;
  const currentBaselineDate = liveDate
    ? (typeof liveDate === 'string' ? liveDate.split('T')[0] : new Date(liveDate).toISOString().split('T')[0])
    : (stats?.as_of_date ?? '2025-12-31');

  const [activeResult, setActiveResult] = useState<ScenarioSubmitResponse | null>(null);
  const [sessionHistory, setSessionHistory] = useState<ScenarioRunRecord[]>([]);
  const pastRunsMap = useRef<Map<string, ScenarioSubmitResponse>>(new Map());

  const submitMutation = useScenarioSubmitMutation();

  const handleRunScenario = (params: ScenarioSubmitRequest) => {
    const requestPayload: ScenarioSubmitRequest = {
      ...params,
      current_aspi: params.current_aspi ?? currentBaselineAspi,
    };
    submitMutation.mutate(requestPayload, {
      onSuccess: (data) => {
        setActiveResult(data);
        pastRunsMap.current.set(data.scenario_id, data);

        // Add to UI session history
        const record: ScenarioRunRecord = {
          id: data.scenario_id,
          timestamp: new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Colombo' }),
          headline: data.headline,
          category: data.category_label,
          trueReturnPct: data.scenarios.TRUE.expected_return_pct,
          falseReturnPct: data.scenarios.FALSE.expected_return_pct,
          targetAspi: data.scenarios.TRUE.target_aspi,
          direction: data.expected_direction,
          evidenceStrength: data.evidence_strength,
        };
        setSessionHistory((prev) => [record, ...prev.filter((p) => p.id !== data.scenario_id)]);
      },
    });
  };

  // Restore past session run
  const handleRestoreRun = (runId: string) => {
    const cached = pastRunsMap.current.get(runId);
    if (cached) {
      setActiveResult(cached);
    }
  };

  // Auto-run if URL query params contain a complete headline
  useEffect(() => {
    if (headlineParam && !activeResult && !submitMutation.isPending) {
      handleRunScenario({
        headline: headlineParam,
        description: '',
        publication_date: dateParam || currentBaselineDate || '',
        category: categoryParam || undefined,
        sector: sectorParam || undefined,
        current_aspi: currentBaselineAspi,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [headlineParam, currentBaselineAspi]);

  // Preset scenarios for instant testing
  const presets = [
    {
      title: 'Presidential Election Declaration',
      headline: 'Election Commission announces presidential election proclamation for September',
      category: 'political',
      desc: 'National polling schedule officially confirmed by Election Secretariat.',
    },
    {
      title: 'Central Bank Policy Rate Reduction',
      headline: 'Central Bank unexpectedly cuts policy interest rates by 100 basis points',
      category: 'monetary',
      desc: 'Monetary Board eases policy stance to stimulate private sector credit.',
    },
    {
      title: 'IMF Tranche Disbursement Approved',
      headline: 'IMF Executive Board approves third review and releases debt tranche',
      category: 'fiscal',
      desc: 'Multilateral lender endorses fiscal transformation benchmarks and revenue targets.',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Breadcrumbs & Header */}
      <div className="space-y-2">
        <Breadcrumbs
          items={[
            { label: 'Home', to: '/' },
            { label: 'Scenario Predictor', to: '/predictor' },
          ]}
        />
        <PageHeader
          title="Political Scenario Predictor"
          description="Conditional counterfactual forecasting engine estimating Colombo Stock Exchange (CSE) ASPI trajectories under political events & macroeconomic shocks."
        />
      </div>

      {/* Input Panel */}
      <ScenarioInputPanel
        onSubmit={handleRunScenario}
        isLoading={submitMutation.isPending}
        prefillNewsId={newsIdParam}
        onClearPrefill={() => {
          const next = new URLSearchParams(searchParams);
          next.delete('news');
          setSearchParams(next);
        }}
        latestAspiValue={currentBaselineAspi}
        latestAspiDate={currentBaselineDate}
      />

      {/* Error State */}
      {submitMutation.isError && (
        <ContractError
          error={submitMutation.error}
          endpoint="/api/v1/scenario"
          onRetry={() => submitMutation.reset()}
        />
      )}

      {/* Result Display */}
      {activeResult && !submitMutation.isPending && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Result Summary Band */}
          <ScenarioResultSummaryBand result={activeResult} />

          {/* Three Panels: Current, TRUE, FALSE */}
          <ScenarioThreePanels result={activeResult} />

          {/* Combined Historical and Fan Chart */}
          <ScenarioCombinedChart result={activeResult} />

          {/* Dimension Comparison Matrix */}
          <ScenarioComparisonMatrix result={activeResult} />

          {/* Historical Evidence Block with CAR mini-chart */}
          <ScenarioEvidenceBlock result={activeResult} />

          {/* Explanation Narrative & Empirical Back-Tests */}
          <ScenarioExplanationAndBacktests result={activeResult} />

          {/* Utilities: Permalink, Exports, and Session History */}
          <ScenarioUtilitiesBar
            result={activeResult}
            sessionHistory={sessionHistory}
            onRestoreRun={handleRestoreRun}
          />
        </div>
      )}

      {/* Empty State with Presets when no simulation has been run */}
      {!activeResult && !submitMutation.isPending && !submitMutation.isError && (
        <div className="rounded-xl border border-dashed border-border bg-surface-subtle/40 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-cobalt/10 text-blue-cobalt">
            <Sparkles className="h-6 w-6" />
          </div>
          <h2 className="mt-3 text-base font-semibold text-text-primary">
            No Scenario Simulated Yet
          </h2>
          <p className="mx-auto mt-1 max-w-lg text-xs text-text-muted">
            Enter a political proclamation or policy news item above, or select a preset scenario below to evaluate counterfactual ASPI distributions with conformal prediction intervals.
          </p>

          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3 text-left">
            {presets.map((preset) => (
              <div
                key={preset.title}
                className="group cursor-pointer rounded-lg border border-border bg-surface-white p-3.5 shadow-xs transition-all hover:border-blue-cobalt hover:shadow-soft"
                onClick={() =>
                  handleRunScenario({
                    headline: preset.headline,
                    description: preset.desc,
                    category: preset.category,
                    publication_date: currentBaselineDate || new Date().toISOString().split('T')[0],
                    current_aspi: currentBaselineAspi,
                  })
                }
              >
                <div className="flex items-center justify-between text-[11px] font-semibold text-blue-navy">
                  <span>{preset.title}</span>
                  <Sparkles className="h-3 w-3 text-blue-cobalt opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-text-secondary">
                  &ldquo;{preset.headline}&rdquo;
                </p>
                <span className="mt-2 inline-block text-[10px] font-medium text-text-muted group-hover:text-blue-cobalt">
                  Click to simulate &rarr;
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
