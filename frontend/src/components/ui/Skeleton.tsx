import React from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'rect' | 'circle' | 'card';
}

export function Skeleton({ className, variant = 'rect', ...props }: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full rounded',
    rect: 'h-8 w-full rounded-button',
    circle: 'h-10 w-10 rounded-full shrink-0',
    card: 'h-32 w-full rounded-card',
  };

  return (
    <div
      aria-hidden="true"
      className={cn(
        'dark:bg-blue-soft/20 animate-pulse bg-surface-subtle',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
