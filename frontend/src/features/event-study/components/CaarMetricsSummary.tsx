import type { EventStudyCaarResponse } from '../types';
import { EventStudyStatCards } from './EventStudyStatCards';

export interface CaarMetricsSummaryProps {
  study?: EventStudyCaarResponse;
}

export function CaarMetricsSummary({ study }: CaarMetricsSummaryProps) {
  return <EventStudyStatCards caarData={study} />;
}
