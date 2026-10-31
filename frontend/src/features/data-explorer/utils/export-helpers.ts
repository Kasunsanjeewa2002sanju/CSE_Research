import type { MarketDataPoint } from './market-calculations';

export function exportMarketDataToCsv(data: MarketDataPoint[], filename?: string): void {
  if (data.length === 0) return;

  const headers = ['Date', 'ASPI', 'SP_SL20', 'Return_Pct', 'Turnover_LKR', 'Shares_Volume'];
  const rows = data.map((p) => [
    p.date,
    p.aspi,
    p.sp_sl20 ?? '',
    p.return !== undefined && p.return !== null ? (p.return * 100).toFixed(4) : '',
    p.turnover ?? '',
    p.volume ?? '',
  ]);

  const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute(
    'download',
    filename || `cse_aspi_dataset_export_${new Date().toISOString().substring(0, 10)}.csv`
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export type SortField = 'date' | 'aspi' | 'return' | 'turnover';
export type SortOrder = 'asc' | 'desc';

export function filterAndSortMarketData(
  points: MarketDataPoint[],
  searchDate: string,
  sortField: SortField,
  sortOrder: SortOrder
): MarketDataPoint[] {
  let result = [...points];

  if (searchDate) {
    result = result.filter((p) => p.date.includes(searchDate));
  }

  result.sort((a, b) => {
    let valA: string | number = a[sortField] ?? 0;
    let valB: string | number = b[sortField] ?? 0;
    if (sortField === 'date') {
      valA = a.date;
      valB = b.date;
    }
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return result;
}
