export interface AspiDataPoint {
  date: string;
  close: number;
  log_return: number;
  volume?: number;
  turnover?: number;
}

export interface AspiHistoryResponse {
  series: AspiDataPoint[];
  total_records: number;
  start_date: string;
  end_date: string;
}
