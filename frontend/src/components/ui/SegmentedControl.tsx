import React from 'react';
import { cn } from '@/lib/utils';

export interface SegmentedOption<T extends string | number> {
  value: T;
  label: string;
  icon?: React.ReactNode;
}

export interface SegmentedControlProps<T extends string | number> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  className?: string;
  'aria-label'?: string;
}

export function SegmentedControl<T extends string | number>({
  options,
  value,
  onChange,
  size = 'sm',
  className,
  'aria-label': ariaLabel = 'Segmented options',
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={cn(
        'border-border/80 inline-flex select-none items-center rounded-button border bg-surface-subtle p-1',
        className
      )}
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={String(opt.value)}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(opt.value)}
            className={cn(
              'transition-standard inline-flex items-center justify-center rounded-button font-mono font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
              size === 'sm' ? 'gap-1.5 px-2.5 py-1 text-xs' : 'gap-2 px-3.5 py-1.5 text-sm',
              isSelected
                ? 'bg-surface-white font-semibold text-blue-navy shadow-soft dark:text-blue-vibrant'
                : 'text-text-muted hover:text-text-primary'
            )}
          >
            {opt.icon && <span className="shrink-0">{opt.icon}</span>}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
