import React from 'react';
import { Card } from './Card';
import { Skeleton } from './Skeleton';
import { ArrowUpRight, ArrowDownRight, Minus, HelpCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StatDelta {
  value: string | number;
  percentage?: number;
  isPositive?: boolean;
  direction?: 'up' | 'down' | 'neutral';
  label?: string;
}

export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
  title?: string;
  value: string | number;
  unit?: string;
  delta?: StatDelta;
  sparkline?: React.ReactNode;
  asOf?: string;
  asOfLabel?: string;
  badgeText?: string;
  sampleSize?: number;
  glossaryTerm?: string;
  glossaryDefinition?: string;
  isStale?: boolean;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  valueClassName?: string;
  statusState?: 'LIVE' | 'DELAYED' | 'CLOSED' | 'STALE' | 'OFFLINE' | 'POLLING';
}

export function StatCard({
  label,
  title,
  value,
  unit,
  delta,
  sparkline,
  asOf,
  asOfLabel,
  badgeText,
  sampleSize,
  glossaryTerm,
  glossaryDefinition,
  isStale = false,
  isLoading = false,
  isError = false,
  errorMessage,
  onRetry,
  valueClassName,
  statusState,
  className,
  ...props
}: StatCardProps) {
  const displayTitle = title || label || '';
  const displayAsOf = asOfLabel || asOf;

  // 1. Loading Skeleton State
  if (isLoading) {
    return (
      <Card
        className={cn('relative flex h-36 flex-col justify-between p-4', className)}
        padding="md"
        {...props}
      >
        <div className="flex items-center justify-between">
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="h-4 w-12" />
        </div>
        <div className="my-2 flex items-baseline justify-between">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-20" />
        </div>
        <div className="border-border/40 flex items-center justify-between border-t pt-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-24" />
        </div>
      </Card>
    );
  }

  // 2. Error State with Retry Affordance
  if (isError) {
    return (
      <Card
        className={cn(
          'relative flex h-36 flex-col justify-between border-rose-500/30 bg-rose-500/5 p-4',
          className
        )}
        padding="md"
        {...props}
      >
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-400">
            {displayTitle}
          </span>
          <span className="rounded bg-rose-500/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-rose-600 dark:text-rose-400">
            Feed Error
          </span>
        </div>
        <div className="my-2">
          <span className="font-mono text-xs text-text-muted">
            {errorMessage || 'Market feed temporarily interrupted.'}
          </span>
        </div>
        <div className="border-border/40 flex items-center justify-between border-t pt-2 font-mono text-[11px]">
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1 font-semibold text-accent hover:underline focus:outline-none"
            >
              <RefreshCw className="h-3 w-3" /> Retry Feed
            </button>
          ) : (
            <span className="text-text-subtle">Reconnecting feed...</span>
          )}
          {displayAsOf && <span className="text-text-subtle">{displayAsOf}</span>}
        </div>
      </Card>
    );
  }

  // Derive direction
  let direction = delta?.direction;
  if (!direction && delta?.isPositive !== undefined) {
    direction = delta.isPositive ? 'up' : 'down';
  } else if (!direction) {
    direction = 'neutral';
  }

  const deltaFormatted =
    delta?.percentage !== undefined
      ? `${delta.isPositive ? '+' : ''}${delta.percentage}%`
      : delta?.value;

  // Sanitize display value: never render blank or NaN (Requirement 4)
  const safeValue =
    value === null ||
    value === undefined ||
    (typeof value === 'number' && Number.isNaN(value)) ||
    (typeof value === 'string' && (value.trim() === '' || value.trim().toLowerCase() === 'nan'))
      ? '—'
      : value;

  // Derive effective badge
  const effectiveBadge =
    badgeText ||
    (statusState === 'CLOSED'
      ? 'Last Close'
      : statusState === 'LIVE'
        ? 'LIVE'
        : undefined);

  return (
    <Card
      className={cn(
        'transition-standard relative flex flex-col justify-between hover:border-border-strong',
        isStale && 'border-data-warning/40',
        statusState === 'CLOSED' && 'bg-surface-subtle/50',
        className
      )}
      padding="md"
      {...props}
    >
      {/* Top Header Row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {statusState === 'LIVE' && (
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
          )}
          <span className="font-mono text-xs font-medium uppercase tracking-wider text-text-muted">
            {displayTitle}
          </span>
          {glossaryDefinition && (
            <span
              className="inline-flex cursor-help text-text-subtle hover:text-text-primary"
              title={`${glossaryTerm ? glossaryTerm + ': ' : ''}${glossaryDefinition}`}
              aria-label={`Definition for ${displayTitle}`}
            >
              <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {effectiveBadge && (
            <span className="bg-accent/15 border-accent/30 rounded-chip border px-2 py-0.5 font-mono text-[10px] font-medium text-accent-hover dark:text-accent">
              {effectiveBadge}
            </span>
          )}
          {sampleSize !== undefined && (
            <span className="dark:bg-blue-soft/30 border-blue-soft/50 rounded-chip border bg-blue-ice px-2 py-0.5 font-mono text-[11px] font-medium text-blue-navy dark:text-blue-vibrant">
              n = {sampleSize.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Main Metric Value & Sparkline Area */}
      <div className="my-3 flex items-baseline justify-between gap-4">
        <div className="flex items-baseline gap-1.5">
          <span
            className={cn(
              'font-mono text-3xl font-extrabold tabular-nums tracking-tight text-text-primary',
              valueClassName
            )}
          >
            {safeValue}
          </span>
          {unit && <span className="font-mono text-sm text-text-muted">{unit}</span>}
        </div>

        {sparkline && <div className="flex h-10 w-24 shrink-0 items-center">{sparkline}</div>}
      </div>

      {/* Footer Details: Delta, Stale flag, As-Of */}
      <div className="border-border/40 flex flex-wrap items-center justify-between gap-2 border-t pt-2 font-mono text-[11px]">
        {delta ? (
          <div
            className={cn(
              'inline-flex items-center gap-1 font-semibold',
              direction === 'up' && 'text-data-up',
              direction === 'down' && 'text-data-down',
              direction === 'neutral' && 'text-text-muted'
            )}
          >
            {direction === 'up' && (
              <ArrowUpRight className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            )}
            {direction === 'down' && (
              <ArrowDownRight className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            )}
            {direction === 'neutral' && (
              <Minus className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            )}
            <span>{deltaFormatted}</span>
            {delta.label && <span className="font-normal text-text-subtle">({delta.label})</span>}
          </div>
        ) : (
          <span />
        )}

        <div className="flex items-center gap-2 text-text-subtle">
          {isStale && (
            <span className="rounded bg-data-warning-subtle px-1.5 py-0.5 font-semibold text-data-warning">
              Stale
            </span>
          )}
          {displayAsOf && (
            <span>
              {displayAsOf.startsWith('As of:') || displayAsOf.startsWith('Last Close:')
                ? displayAsOf
                : `As of: ${displayAsOf}`}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
