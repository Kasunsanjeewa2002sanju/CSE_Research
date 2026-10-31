import type { EventStudyPerEventItem } from '../types';

export function exportEventStudyCsv(
  items: EventStudyPerEventItem[],
  filename = 'cse_event_study_records.csv'
): void {
  if (!items || items.length === 0) return;

  const headers = [
    'Event ID',
    'Event Name',
    'Election Type',
    'Stage',
    'Date (Mapped)',
    'Year',
    'Window',
    'CAR (%)',
    'Brown-Warner SE (%)',
    'CI Lower 95% (%)',
    'CI Upper 95% (%)',
    't-statistic',
    'p-value (Raw)',
    'Permutation p-value',
    'BH FDR Corrected p-value',
    'Overlapping (<=30TD)',
    'ASPI Before',
    'ASPI After',
    'Market Change (%)',
    'Significance Badge',
  ];

  const escapeCsv = (val: unknown): string => {
    if (val === undefined || val === null) return '';
    const str = String(val);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const rows = items.map((r) =>
    [
      r.event_id,
      r.event_name,
      r.election_type,
      r.stage,
      r.date,
      r.year,
      r.window,
      r.car,
      r.bw_se,
      r.ci_lower,
      r.ci_upper,
      r.t_stat,
      r.p_value,
      r.permutation_p_val,
      r.corrected_p_val,
      r.is_overlapping ? 'Yes' : 'No',
      r.aspi_before,
      r.aspi_after,
      r.change_pct,
      r.significance_badge ?? 'Inconclusive',
    ]
      .map(escapeCsv)
      .join(',')
  );

  const csvContent = [headers.join(','), ...rows].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
