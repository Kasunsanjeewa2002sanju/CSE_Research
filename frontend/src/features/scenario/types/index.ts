import type {
  ScenarioSubmitRequest,
  ScenarioSubmitResponse,
  ScenarioHorizon,
  ScenarioPanel,
  ScenarioEvidence,
  ScenarioComparisonRow,
  ScenarioComparisonMatrix,
  ScenarioBacktestItem,
  ScenarioBacktestsSummary,
  ScenarioBacktestsResponse,
} from '@/api/types';

export type {
  ScenarioSubmitRequest,
  ScenarioSubmitResponse,
  ScenarioHorizon,
  ScenarioPanel,
  ScenarioEvidence,
  ScenarioComparisonRow,
  ScenarioComparisonMatrix,
  ScenarioBacktestItem,
  ScenarioBacktestsSummary,
  ScenarioBacktestsResponse,
};

// UI Session history record
export interface ScenarioRunRecord {
  id: string;
  timestamp: string;
  headline: string;
  category: string;
  trueReturnPct: number;
  falseReturnPct: number;
  targetAspi: number;
  direction: string;
  evidenceStrength: string;
}

// Backward-compatibility parameter types for legacy helpers
export interface ScenarioParams {
  headline?: string;
  description?: string;
  category?: string;
  event_category?: string;
  event_type?: string;
  margin?: number;
  turnout?: number;
  expected_turnout_pct?: number;
  expected_margin_pct?: number;
  lead_party?: string;
  market_regime?: 'bull' | 'bear' | 'neutral';
  horizon_days?: number;
}

export interface ScenarioResult {
  predicted_return: number;
  conformal_80_lower: number;
  conformal_80_upper: number;
  conformal_95_lower: number;
  conformal_95_upper: number;
  model_used: string;
}
