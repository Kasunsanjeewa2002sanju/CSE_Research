/**
 * Core Application & API Envelope Types (Rule FR4 & FR5)
 */

export interface ApiMetadata {
  as_of_date: string;
  data_version: string;
  pipeline_stage?: string;
  sample_size?: number;
  disclaimer?: string;
  is_stale?: boolean;
}

export interface ApiResponse<T> {
  data: T;
  meta: ApiMetadata;
}

export interface MetricDefinition {
  metric_id: string;
  name: string;
  definition: string;
  formula?: string;
  benchmark?: string;
}

export interface SystemStatus {
  status: string;
  pipeline_version: string;
  active_stages: number[];
  as_of_date: string;
  is_stale: boolean;
  champion_model?: string;
  data_points?: number;
}
