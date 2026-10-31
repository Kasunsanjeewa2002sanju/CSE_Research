import { useState } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { LineChart, Grid3X3, TableProperties, BookOpen } from 'lucide-react';
import {
  useEventStudyCaarQuery,
  useEventStudyHeatmapQuery,
  useEventStudyPerEventQuery,
  useEventStudySummaryQuery,
} from '../hooks/useEventStudyData';
import { EventStudyControls } from '../components/EventStudyControls';
import { EventStudyStatCards } from '../components/EventStudyStatCards';
import { CaarTrajectoryChart } from '../components/CaarTrajectoryChart';
import { EventStudyHeatmapChart } from '../components/EventStudyHeatmapChart';
import { EventStudyForestPlot } from '../components/EventStudyForestPlot';
import { PermutationNullChart } from '../components/PermutationNullChart';
import { EventStudyPastRecordsTable } from '../components/EventStudyPastRecordsTable';
import { EventStudyInterpretationPanel } from '../components/EventStudyInterpretationPanel';
import type { TrajectoryDisplayMode } from '../types';

const STAGE_NUMBER_TO_KEY: Record<number, string> = {
  1: 'announcement',
  2: 'nomination_start',
  3: 'nomination_end',
  4: 'polling',
  5: 'result',
  6: 'government_formation',
};

export default function EventStudyPage() {
  const [electionType, setElectionType] = useState('All');
  const [stageNumber, setStageNumber] = useState(4); // Default to Polling Day (t=0)
  const [expectedReturnModel, setExpectedReturnModel] = useState('mean_adjusted');
  const [estimationWindow, setEstimationWindow] = useState(15);
  const [eventWindow, setEventWindow] = useState('[-7,+7]');
  const [includeOverlapping, setIncludeOverlapping] = useState(true);
  const [trajectoryDisplayMode, setTrajectoryDisplayMode] = useState<TrajectoryDisplayMode>('both');
  const [activeTab, setActiveTab] = useState('trajectory');

  const stageKey = STAGE_NUMBER_TO_KEY[stageNumber] ?? 'polling';

  // 1. Live CAAR Query
  const { data: caarData, isLoading: caarLoading } = useEventStudyCaarQuery({
    window: eventWindow,
    election_type: electionType,
    stage: stageKey,
    model_type: expectedReturnModel,
    estimation_len: estimationWindow,
    include_overlapping: includeOverlapping,
  });

  // 2. Heatmap Matrix Query
  const { data: heatmapData, isLoading: heatmapLoading } = useEventStudyHeatmapQuery();

  // 3. Per-Event Records Query for Forest Plot and Past Records Table
  const { data: perEventData, isLoading: perEventLoading } = useEventStudyPerEventQuery({
    window: eventWindow,
    election_type: electionType,
    stage: stageKey,
    include_overlapping: includeOverlapping,
  });

  // 4. Research Interpretation Summary Query
  const { data: summaryData, isLoading: summaryLoading } = useEventStudySummaryQuery();

  const hasModelledTrajectory = Boolean(caarData?.modelled_trajectory);

  return (
    <PageContainer
      title="Event Study Explorer"
      description="Econometric Cumulative Abnormal Return (CAAR) analysis isolating CSE market response to Sri Lankan political events across six electoral stages."
      breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Event Study' }]}
    >
      <div className="space-y-6">
        {/* 1. Global Interactive Controls */}
        <EventStudyControls
          electionType={electionType}
          onElectionTypeChange={setElectionType}
          stageNumber={stageNumber}
          onStageNumberChange={setStageNumber}
          expectedReturnModel={expectedReturnModel}
          onExpectedReturnModelChange={setExpectedReturnModel}
          estimationWindow={estimationWindow}
          onEstimationWindowChange={setEstimationWindow}
          eventWindow={eventWindow}
          onEventWindowChange={setEventWindow}
          includeOverlapping={includeOverlapping}
          onIncludeOverlappingChange={setIncludeOverlapping}
          hasModelledTrajectory={hasModelledTrajectory}
          trajectoryDisplayMode={trajectoryDisplayMode}
          onTrajectoryDisplayModeChange={setTrajectoryDisplayMode}
        />

        {/* 2. Statistical KPI Summary Cards & Small Sample Alert */}
        <EventStudyStatCards caarData={caarData} isLoading={caarLoading} />

        {/* 3. Analytical Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-2 md:grid-cols-4">
            <TabsTrigger value="trajectory" className="gap-2 text-xs">
              <LineChart className="h-3.5 w-3.5" />
              <span>Trajectory &amp; Impulses</span>
            </TabsTrigger>
            <TabsTrigger value="heatmap" className="gap-2 text-xs">
              <Grid3X3 className="h-3.5 w-3.5" />
              <span>Cross-Stage Matrix</span>
            </TabsTrigger>
            <TabsTrigger value="records" className="gap-2 text-xs">
              <TableProperties className="h-3.5 w-3.5" />
              <span>Past Records &amp; Audit</span>
            </TabsTrigger>
            <TabsTrigger value="interpretation" className="gap-2 text-xs">
              <BookOpen className="h-3.5 w-3.5" />
              <span>Interpretation &amp; Caveats</span>
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: Trajectory, AR Bars, Forest Plot & Permutation Histogram */}
          <TabsContent value="trajectory" className="space-y-6">
            <CaarTrajectoryChart
              caarData={caarData}
              displayMode={trajectoryDisplayMode}
              isLoading={caarLoading}
            />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <PermutationNullChart
                distribution={caarData?.permutation_distribution}
                isLoading={caarLoading}
              />
              <EventStudyForestPlot
                items={perEventData?.items ?? []}
                windowDays={eventWindow}
                isLoading={perEventLoading}
              />
            </div>
          </TabsContent>

          {/* TAB 2: Heatmap Matrix */}
          <TabsContent value="heatmap" className="space-y-4">
            <EventStudyHeatmapChart heatmapData={heatmapData} isLoading={heatmapLoading} />
          </TabsContent>

          {/* TAB 3: Past Records Table */}
          <TabsContent value="records" className="space-y-4">
            <EventStudyPastRecordsTable
              items={perEventData?.items ?? []}
              windowDays={eventWindow}
              warnSmallSample={caarData?.warn_small_sample}
              smallSampleWarningText={caarData?.small_sample_warning_text}
              isLoading={perEventLoading}
            />
          </TabsContent>

          {/* TAB 4: Interpretation & Caveats */}
          <TabsContent value="interpretation" className="space-y-4">
            <EventStudyInterpretationPanel summary={summaryData} isLoading={summaryLoading} />
          </TabsContent>
        </Tabs>
      </div>
    </PageContainer>
  );
}
