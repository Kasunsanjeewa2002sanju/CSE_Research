import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { Column } from '@/components/ui/Table';
import type { EChartsOption } from '@/components/charts';
import type { DataAudit } from '@/api/types';

export function createTradingDaysOption(
  tradingDaysPerYear?: DataAudit['trading_days_per_year']
): EChartsOption {
  if (!tradingDaysPerYear) return {};

  const years = tradingDaysPerYear.map((d: { year: number }) => String(d.year));
  const counts = tradingDaysPerYear.map((d: { year: number; trading_days: number }) => {
    const isUnusual = d.year === 2020 || d.year === 2022 || d.trading_days < 220;
    return {
      value: d.trading_days,
      itemStyle: {
        color: isUnusual ? '#E39B0B' : '#1246B3',
      },
    };
  });

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const list = params as Array<{ name: string; value: number }>;
        const item = list[0];
        if (!item) return '';
        const year = item.name;
        const days = item.value;
        let note = '';
        if (year === '2020')
          note = '<br/><span style="color:#E39B0B">COVID-19 national market closure</span>';
        if (year === '2022')
          note = '<br/><span style="color:#E39B0B">Economic crisis & currency float halts</span>';
        return `<strong>${year}</strong>: ${days} Trading Days${note}`;
      },
    },
    grid: { left: '3%', right: '3%', bottom: '10%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: years,
      axisLabel: { interval: 2, rotate: 45, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'Days',
      min: 180,
      max: 260,
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    series: [
      {
        name: 'Trading Days',
        type: 'bar',
        data: counts,
      },
    ],
  };
}

export const FALLBACK_LARGE_MOVES = [
  {
    date: '2009-05-18',
    return_pct: 12.3,
    flag: 'CIRCUIT_BREAKER_UP',
    note: 'Civil war conclusion proclamation & rally',
  },
  {
    date: '2022-04-25',
    return_pct: -12.6,
    flag: 'CIRCUIT_BREAKER_DOWN',
    note: 'Resumption after crisis halt & sovereign debt default',
  },
  {
    date: '2020-03-20',
    return_pct: -8.4,
    flag: 'VOLATILITY_OUTLIER',
    note: 'Initial COVID-19 pandemic panic sell-off',
  },
  {
    date: '2008-10-24',
    return_pct: -8.2,
    flag: 'VOLATILITY_OUTLIER',
    note: 'Global Financial Crisis Lehman contagion',
  },
  {
    date: '2020-05-11',
    return_pct: 8.9,
    flag: 'CIRCUIT_BREAKER_UP',
    note: 'Post-lockdown electronic trading resumption rally',
  },
  {
    date: '2022-03-31',
    return_pct: -8.1,
    flag: 'VOLATILITY_OUTLIER',
    note: 'Emergency interest rate hike & sovereign stress',
  },
];

export interface LargeMoveItem {
  date: string;
  return_pct: number;
  flag: string;
  note?: string;
}

export interface DictionaryItem {
  column: string;
  type: string;
  description: string;
  non_null_count: number;
}

export const largeMoveColumns: Column<LargeMoveItem>[] = [
  {
    key: 'date',
    header: 'Trading Date',
    render: (val) => <span className="font-mono font-medium">{String(val || '')}</span>,
  },
  {
    key: 'return_pct',
    header: 'Daily Return',
    className: 'text-right',
    render: (val) => {
      const num = typeof val === 'number' ? val : Number(val) || 0;
      const isPos = num >= 0;
      return (
        <span
          className={`inline-flex items-center gap-1 font-mono font-bold ${isPos ? 'text-data-up' : 'text-data-down'}`}
        >
          {isPos ? (
            <ArrowUpRight className="h-3.5 w-3.5" />
          ) : (
            <ArrowDownRight className="h-3.5 w-3.5" />
          )}
          {isPos ? '+' : ''}
          {num.toFixed(2)}%
        </span>
      );
    },
  },
  {
    key: 'flag',
    header: 'Audit Flag',
    render: (val) => {
      const str = String(val || '');
      return (
        <Badge
          variant={str.includes('UP') ? 'success' : str.includes('DOWN') ? 'danger' : 'warning'}
          size="sm"
          className="font-mono text-[10px]"
        >
          {str}
        </Badge>
      );
    },
  },
  {
    key: 'note',
    header: 'Historical Context',
    render: (val) => <span className="text-xs text-text-muted">{String(val || '')}</span>,
  },
];

export const dictionaryColumns: Column<DictionaryItem>[] = [
  {
    key: 'column',
    header: 'Column Name',
    render: (val) => (
      <code className="rounded bg-surface-subtle px-1.5 py-0.5 font-mono text-xs font-semibold text-blue-navy dark:text-blue-vibrant">
        {String(val || '')}
      </code>
    ),
  },
  {
    key: 'type',
    header: 'Data Type',
    render: (val) => <span className="font-mono text-xs text-text-muted">{String(val || '')}</span>,
  },
  {
    key: 'description',
    header: 'Description & Scope',
    render: (val) => <span className="text-xs">{String(val || '')}</span>,
  },
  {
    key: 'non_null_count',
    header: 'Non-Null Rows',
    className: 'text-right',
    render: (val) => (
      <span className="font-mono text-xs">
        {typeof val === 'number' ? val.toLocaleString() : String(val || '')}
      </span>
    ),
  },
];
