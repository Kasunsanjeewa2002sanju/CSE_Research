export interface OverviewSummary {
  aspi_current: number;
  daily_return: number;
  sample_size_events: number;
  champion_model_name: string;
  champion_oos_r2: number;
  champion_directional_accuracy: number;
  data_as_of: string;
  is_stale: boolean;
  disclaimer: string;
}
