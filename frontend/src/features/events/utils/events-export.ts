import type { PoliticalEvent } from '@/api/types';

export function exportEventsToCsv(events: PoliticalEvent[]): void {
  const headers = [
    'Event ID',
    'Event Name',
    'Category',
    'Reaction Date (Mapped)',
    'Raw Date',
    'Gap (Days)',
    'Sample Period (2009-2025)',
    'Overlapping Flag (<=30TD)',
    'Added by Researcher',
    'Turnout (%)',
    'Margin (%)',
    'Elected Administration',
    'Sources',
  ];

  const rows = events.map((e) => [
    e.id,
    `"${(e.name || '').replace(/"/g, '""')}"`,
    e.category,
    e.mapped_date || e.mappedTradingDate || e.date,
    e.raw_date || e.rawDate || e.date,
    e.gap_days ?? e.gapDays ?? 0,
    e.sample_period ? 'TRUE' : 'FALSE',
    e.is_overlapping ? 'TRUE' : 'FALSE',
    e.added_by_researcher ? 'TRUE' : 'FALSE',
    e.turnout_pct ?? '',
    e.margin_pct ?? '',
    `"${(e.winner_party || '').replace(/"/g, '""')}"`,
    `"${(e.sources || []).join('; ').replace(/"/g, '""')}"`,
  ]);

  const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute(
    'download',
    `cse_political_events_catalog_${new Date().toISOString().slice(0, 10)}.csv`
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
