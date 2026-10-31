import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MetricDefinition } from '@/types/common';

export interface TooltipProps {
  content?: React.ReactNode;
  glossaryMetric?: MetricDefinition;
  glossaryTerm?: string;
  glossaryDefinition?: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export function Tooltip({
  content,
  glossaryMetric,
  glossaryTerm,
  glossaryDefinition,
  children,
  position = 'top',
  className,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const hasGlossary = !!glossaryMetric || (!!glossaryTerm && !!glossaryDefinition);
  const termName = glossaryMetric?.name || glossaryTerm;
  const termDefinition = glossaryMetric?.definition || glossaryDefinition;

  return (
    <span
      className={cn('group relative inline-flex cursor-help items-center', className)}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}

      {isVisible && (
        <span
          role="tooltip"
          className={cn(
            'animate-fade-in pointer-events-none absolute z-50 w-64 max-w-xs rounded-card border border-border bg-surface-card p-3 text-left shadow-elevated',
            positions[position]
          )}
        >
          {hasGlossary ? (
            <div className="space-y-1.5 font-sans">
              <div className="flex items-center gap-1.5 font-heading text-xs font-bold text-blue-navy dark:text-blue-vibrant">
                <HelpCircle className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
                <span>{termName}</span>
              </div>
              <p className="text-[11px] leading-relaxed text-text-muted">{termDefinition}</p>
              {glossaryMetric?.formula && (
                <div className="border-border/60 rounded border-t bg-surface-subtle p-1 pt-1 font-mono text-[10px] text-text-primary">
                  Formula: {glossaryMetric.formula}
                </div>
              )}
              {glossaryMetric?.benchmark && (
                <div className="font-mono text-[10px] text-accent-hover">
                  Benchmark: {glossaryMetric.benchmark}
                </div>
              )}
            </div>
          ) : (
            <div className="font-sans text-xs leading-relaxed text-text-primary">{content}</div>
          )}
        </span>
      )}
    </span>
  );
}
