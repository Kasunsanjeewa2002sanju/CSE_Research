import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'subtle' | 'elevated' | 'bordered';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({ className, variant = 'default', padding = 'md', ...props }: CardProps) {
  const variants = {
    default: 'bg-surface-card border border-border shadow-soft',
    subtle: 'bg-surface-subtle border border-border/70',
    elevated: 'bg-surface-card border border-border/80 shadow-card',
    bordered: 'bg-surface-card border-2 border-border',
  };

  const paddings = {
    none: 'p-0',
    sm: 'p-3 sm:p-4',
    md: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  return (
    <div
      className={cn(
        'transition-standard overflow-hidden rounded-card text-text-primary',
        variants[variant],
        paddings[padding],
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('border-border/50 mb-4 flex flex-col space-y-1.5 border-b pb-4', className)}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('font-heading text-lg font-bold tracking-tight text-text-primary', className)}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-xs leading-relaxed text-text-muted', className)} {...props} />;
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('text-sm', className)} {...props} />;
}

export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'border-border/50 mt-4 flex items-center justify-between border-t pt-4 text-xs text-text-muted',
        className
      )}
      {...props}
    />
  );
}
