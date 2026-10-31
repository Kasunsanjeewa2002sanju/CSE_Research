import type {
  ProtocolPhase,
  TargetDefinition,
  LeakageTestStatus,
  LeakageTestItem,
  PipelineStage,
  BaselineDefinition,
  ProtocolResponse,
  FeatureDictionaryItem,
  PhaseEventCoverageItem,
  FeatureDictionaryResponse,
} from '@/api/types';

export type {
  ProtocolPhase,
  TargetDefinition,
  LeakageTestStatus,
  LeakageTestItem,
  PipelineStage,
  BaselineDefinition,
  ProtocolResponse,
  FeatureDictionaryItem,
  PhaseEventCoverageItem,
  FeatureDictionaryResponse,
};

export interface ProtocolRule {
  id: string;
  name: string;
  category: string;
  description: string;
  enforcement: string;
}

export interface MethodologyResponse {
  phases_count: number;
  protocol_rules: ProtocolRule[];
  leakage_audit_status: string;
}

export type FeatureSetFilter = 'all' | 'A' | 'B' | 'C';
export type FeatureGroupFilter = 'all' | 'price' | 'activity' | 'event';

export interface FeatureFilters {
  featureSet: FeatureSetFilter;
  group: FeatureGroupFilter;
  search: string;
}

export type MethodologyTab = 'protocol' | 'pipeline' | 'features' | 'leakage' | 'baselines';
