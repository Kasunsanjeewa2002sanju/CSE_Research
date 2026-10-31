import React from 'react';
import { cn } from '@/lib/utils';

export interface KeyValueItem {
  key: string;
  label?: string;
  value: React.ReactNode;
  hint?: string;
  highlight?: boolean;
}

export interface KeyValueListProps {
  items: KeyValueItem[];
  dense?: boolean;
  className?: string;
}

export function KeyValueList({ items, dense = false, className }: KeyValueListProps) {
  return (
    <dl
      className={cn(
        'divide-border/60 divide-y overflow-hidden rounded-card border border-border bg-surface-card font-mono text-xs',
        className
      )}
    >
      {items.map((item) => (
        <div
          key={item.key}
          className={cn(
            'transition-standard flex flex-col justify-between gap-1 sm:flex-row sm:items-center',
            dense ? 'px-3 py-2' : 'px-4 py-3',
            item.highlight ? 'bg-blue-ice/60 dark:bg-blue-soft/30' : 'hover:bg-surface-subtle/40'
          )}
        >
          <dt className="flex items-center gap-1.5 text-text-muted">
            <span>{item.label || item.key}</span>
            {item.hint && (
              <span className="font-sans text-[10px] text-text-subtle">({item.hint})</span>
            )}
          </dt>
          <dd className="text-left font-semibold tabular-nums text-text-primary sm:text-right">
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
