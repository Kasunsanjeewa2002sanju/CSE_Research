/**
 * Auto-generated API Types from OpenAPI Schema
 * Do NOT edit manually. Run 'npm run gen:api' to regenerate from backend OpenAPI.
 */

export interface ApiMetadataContract {
  as_of_date: string;
  data_version: string;
  pipeline_stage?: string;
  sample_size?: number;
  disclaimer?: string;
  is_stale?: boolean;
}

export interface SystemStatusContract {
  status: string;
  pipeline_version: string;
  active_stages: number[];
  as_of_date: string;
  is_stale: boolean;
  champion_model?: string;
  data_points?: number;
}
