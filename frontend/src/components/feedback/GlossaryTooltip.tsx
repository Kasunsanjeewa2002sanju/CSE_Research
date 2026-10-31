import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MetricDefinition } from '@/types/common';

export interface GlossaryTooltipProps {
  metric: MetricDefinition;
  children?: React.ReactNode;
  className?: string;
}

export function GlossaryTooltip({ metric, children, className }: GlossaryTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span className={cn('group relative inline-flex cursor-help items-center gap-1', className)}>
      {children && (
        <span className="border-muted-foreground/60 border-b border-dotted">{children}</span>
      )}
      <button
        type="button"
        aria-label={`Definition of ${metric.name}`}
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
        className="text-muted-foreground hover:text-foreground focus-visible:ring-primary rounded focus-visible:outline-none focus-visible:ring-1"
      >
        <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          role="tooltip"
          className="bg-popover text-popover-foreground animate-fade-in pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-72 -translate-x-1/2 rounded-lg border border-border p-3 font-sans text-xs shadow-lg"
        >
          <div className="text-primary font-heading font-semibold">{metric.name}</div>
          <div className="text-muted-foreground mt-1 leading-normal">{metric.definition}</div>
          {metric.formula && (
            <div className="text-foreground bg-muted/40 mt-1.5 rounded border-t border-border p-1 pt-1.5 font-mono text-[11px]">
              Formula: {metric.formula}
            </div>
          )}
          {metric.benchmark && (
            <div className="text-market-accent mt-1 text-[11px]">Guideline: {metric.benchmark}</div>
          )}
        </div>
      )}
    </span>
  );
}
