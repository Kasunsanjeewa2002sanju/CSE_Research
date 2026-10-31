import { useState } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { useProtocolQuery, useFeatureDictionaryQuery } from '../hooks/useMethodologyData';
import { useMeta } from '@/context/MetaContext';
import { PhaseTimeline } from '../components/PhaseTimeline';
import { PipelineFlow } from '../components/PipelineFlow';
import { FeatureDictionary } from '../components/FeatureDictionary';
import { TestBoard } from '../components/TestBoard';
import { BaselinesGlossary } from '../components/BaselinesGlossary';
import type { MethodologyTab } from '../types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export default function MethodologyPage() {
  const [activeTab, setActiveTab] = useState<MethodologyTab>('protocol');
  const { asOfDate, meta } = useMeta();

  const {
    data: protocolData,
    isLoading: isProtocolLoading,
    isError: isProtocolError,
    error: protocolError,
    refetch: refetchProtocol,
  } = useProtocolQuery();

  const {
    data: featureData,
    isLoading: isFeatureLoading,
    isError: isFeatureError,
    error: featureError,
    refetch: refetchFeatures,
  } = useFeatureDictionaryQuery();

  const isLoading = isProtocolLoading || isFeatureLoading;
  const isError = isProtocolError || isFeatureError;

  return (
    <PageContainer
      title="Research Methodology & Protocol Guardrails"
      description="Zero-lookahead validation protocol, walk-forward expanding window splits, backend pipeline flow, and engineered causal feature dictionary."
      badge={asOfDate ? <Badge variant="outline" className="font-mono text-xs">As of: {asOfDate}</Badge> : undefined}
      breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Methodology' }]}
    >
      <div className="space-y-6">
        {/* Navigation Tabs Bar */}
        <div className="border-b border-border">
          <nav className="-mb-px flex flex-wrap gap-2 sm:gap-4" aria-label="Methodology Sections">
            <button
              onClick={() => setActiveTab('protocol')}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'protocol'
                  ? 'border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
              }`}
              role="tab"
              aria-selected={activeTab === 'protocol'}
            >
              <span>Walk-Forward Protocol</span>
              <Badge
                variant={activeTab === 'protocol' ? 'default' : 'secondary'}
                className="font-mono text-[10px]"
              >
                {protocolData?.phases.length ?? 5} Phases
              </Badge>
            </button>

            <button
              onClick={() => setActiveTab('pipeline')}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'pipeline'
                  ? 'border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
              }`}
              role="tab"
              aria-selected={activeTab === 'pipeline'}
            >
              <span>Pipeline Flow</span>
              <Badge
                variant={activeTab === 'pipeline' ? 'default' : 'secondary'}
                className="font-mono text-[10px]"
              >
                {protocolData?.pipeline_stages?.length ?? 13} Stages
              </Badge>
            </button>

            <button
              onClick={() => setActiveTab('features')}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'features'
                  ? 'border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
              }`}
              role="tab"
              aria-selected={activeTab === 'features'}
            >
              <span>Feature Sets</span>
              <Badge
                variant={activeTab === 'features' ? 'default' : 'secondary'}
                className="font-mono text-[10px]"
              >
                {featureData?.total_features ?? 57} Feats
              </Badge>
            </button>

            <button
              onClick={() => setActiveTab('leakage')}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'leakage'
                  ? 'border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
              }`}
              role="tab"
              aria-selected={activeTab === 'leakage'}
            >
              <span>Leakage Board</span>
              <Badge
                variant={activeTab === 'leakage' ? 'default' : 'secondary'}
                className="font-mono text-[10px] text-teal-600 dark:text-teal-400"
              >
                {protocolData?.leakage_tests?.length ?? 6} Tests
              </Badge>
            </button>

            <button
              onClick={() => setActiveTab('baselines')}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'baselines'
                  ? 'border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
              }`}
              role="tab"
              aria-selected={activeTab === 'baselines'}
            >
              <span>Baselines & Glossary</span>
              <Badge
                variant={activeTab === 'baselines' ? 'default' : 'secondary'}
                className="font-mono text-[10px]"
              >
                {protocolData?.baselines?.length ?? 4} Baselines
              </Badge>
            </button>
          </nav>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex min-h-[400px] flex-col items-center justify-center gap-3 rounded-lg border border-border p-8">
            <div className="border-primary h-8 w-8 animate-spin rounded-full border-2 border-t-transparent" />
            <p className="text-muted-foreground font-mono text-xs">
              Loading research protocol, pipeline status, and feature dictionary...
            </p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-red-900 dark:text-red-200">
            <h3 className="font-bold">Failed to load methodology specifications</h3>
            <p className="mt-1 text-xs">
              {(protocolError as Error)?.message ||
                (featureError as Error)?.message ||
                'Contract validation error'}
            </p>
            <div className="mt-4 flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  refetchProtocol();
                  refetchFeatures();
                }}
              >
                Retry Request
              </Button>
            </div>
          </div>
        )}

        {/* Content Tabs */}
        {!isLoading && !isError && protocolData && featureData && (
          <div className="space-y-6">
            {activeTab === 'protocol' && (
              <PhaseTimeline
                phases={protocolData.phases}
                targetDefinitions={protocolData.target_definitions}
              />
            )}

            {activeTab === 'pipeline' && (
              <PipelineFlow stages={protocolData.pipeline_stages ?? []} />
            )}

            {activeTab === 'features' && (
              <FeatureDictionary
                features={featureData.features}
                phaseCoverage={featureData.phase_event_coverage ?? []}
              />
            )}

            {activeTab === 'leakage' && (
              <TestBoard
                tests={protocolData.leakage_tests ?? []}
                overallStatus={protocolData.leakage_test_status}
              />
            )}

            {activeTab === 'baselines' && (
              <BaselinesGlossary
                baselines={protocolData.baselines ?? []}
                metrics={meta?.metric_glossary ?? []}
              />
            )}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
