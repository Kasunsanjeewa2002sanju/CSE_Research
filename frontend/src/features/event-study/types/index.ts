import type {
  CaarDataPoint,
  IndividualEventCarPoint,
  IndividualEventStudyPath,
  PermutationBin,
  PermutationDistribution,
  CaarStats,
  EventStudyCaarResponse,
  EventStudySubgroup,
  EventStudySubgroupsResponse,
  HeatmapCell,
  EventStudyHeatmapResponse,
  EventStudyPerEventItem,
  EventStudyPerEventResponse,
  EventStudySummaryResponse,
} from '@/api/types';

export type {
  CaarDataPoint,
  IndividualEventCarPoint,
  IndividualEventStudyPath,
  PermutationBin,
  PermutationDistribution,
  CaarStats,
  EventStudyCaarResponse,
  EventStudySubgroup,
  EventStudySubgroupsResponse,
  HeatmapCell,
  EventStudyHeatmapResponse,
  EventStudyPerEventItem,
  EventStudyPerEventResponse,
  EventStudySummaryResponse,
};

export type EventStudyResponse = EventStudyCaarResponse;

export interface EventStudyFilterParams {
  electionType: string;
  stageNumber: number;
  stageId: string;
  expectedReturnModel: string;
  estimationWindow: number;
  eventWindow: string;
  includeOverlapping: boolean;
}

export type TrajectoryDisplayMode = 'both' | 'actual' | 'predicted';
