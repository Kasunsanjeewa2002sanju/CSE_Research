import React from 'react';
import { cn } from '@/lib/utils';

export type BadgeVariant =
  | 'default'
  | 'navy'
  | 'accent'
  | 'outline'
  | 'secondary'
  | 'warning'
  | 'danger'
  | 'success'
  | 'primary'
  | 'neutral'
  | 'market-up'
  | 'market-down'
  | 'market-neutral'
  | 'impact-high'
  | 'impact-medium'
  | 'impact-low'
  | 'evidence-strong'
  | 'evidence-moderate'
  | 'evidence-weak'
  | 'event-presidential'
  | 'event-parliamentary'
  | 'event-provincial'
  | 'event-crisis'
  | 'data-up'
  | 'data-down'
  | 'data-warning';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

export function Badge({
  className,
  variant = 'default',
  size = 'sm',
  children,
  ...props
}: BadgeProps) {
  const variants: Record<BadgeVariant, string> = {
    default:
      'bg-blue-ice text-blue-navy dark:bg-blue-soft/30 dark:text-blue-vibrant border-blue-soft/40',
    navy: 'bg-blue-navy text-white border-transparent',
    accent: 'bg-accent/20 text-accent-hover dark:text-accent border-accent/30',
    outline: 'bg-transparent text-text-primary border-border',
    secondary: 'bg-surface-subtle text-text-muted border-border font-medium',
    primary: 'bg-blue-ice text-blue-cobalt border-blue-soft/40 font-medium',
    neutral: 'bg-surface-subtle text-text-muted border-border',

    // Semantic Data / Alerts
    warning: 'bg-data-warning-subtle text-data-warning border-data-warning/30 font-semibold',
    danger: 'bg-data-down-subtle text-data-down border-data-down/30 font-semibold',
    success: 'bg-data-up-subtle text-data-up border-data-up/30 font-semibold',

    // Market status aliases
    'market-up': 'bg-data-up-subtle text-data-up border-data-up/30 font-semibold',
    'market-down': 'bg-data-down-subtle text-data-down border-data-down/30 font-semibold',
    'market-neutral': 'bg-surface-subtle text-text-muted border-border font-medium',

    // Impact Level Tokens
    'impact-high': 'bg-data-down-subtle text-data-down border-data-down/30 font-semibold',
    'impact-medium':
      'bg-data-warning-subtle text-data-warning border-data-warning/30 font-semibold',
    'impact-low': 'bg-blue-ice text-blue-cobalt border-blue-soft/40 font-semibold',

    // Evidence Strength Tokens (Rule FR5)
    'evidence-strong': 'bg-data-up-subtle text-data-up border-data-up/30 font-semibold',
    'evidence-moderate': 'bg-blue-ice text-blue-vibrant border-blue-soft/40',
    'evidence-weak': 'bg-surface-subtle text-text-muted border-border',

    // Event Types
    'event-presidential': 'bg-blue-ice text-blue-navy border-blue-soft/50 font-medium',
    'event-parliamentary':
      'bg-accent-subtle text-accent-hover dark:text-accent border-accent/30 font-medium',
    'event-provincial': 'bg-surface-subtle text-text-muted border-border font-medium',
    'event-crisis': 'bg-data-down-subtle text-data-down border-data-down/30 font-medium',

    // Semantic Data
    'data-up': 'bg-data-up-subtle text-data-up border-data-up/30',
    'data-down': 'bg-data-down-subtle text-data-down border-data-down/30',
    'data-warning': 'bg-data-warning-subtle text-data-warning border-data-warning/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={cn(
        'transition-standard inline-flex select-none items-center gap-1 rounded-chip border font-mono font-medium',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
