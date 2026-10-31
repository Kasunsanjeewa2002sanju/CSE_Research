import React from 'react';
import { cn } from '@/lib/utils';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  'aria-label': string; // Required for WCAG 2.1 AA accessibility (Rule FR6)
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      className,
      variant = 'ghost',
      size = 'md',
      isLoading = false,
      icon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-sans rounded-button transition-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none shrink-0';

    const variants = {
      primary: 'bg-accent text-accent-foreground hover:bg-accent-hover shadow-soft',
      secondary:
        'bg-blue-ice text-blue-navy hover:bg-blue-soft/50 dark:bg-blue-soft/30 dark:text-text-primary',
      outline: 'border border-border bg-surface-white text-text-primary hover:bg-surface-subtle',
      ghost: 'text-text-muted hover:text-text-primary hover:bg-surface-subtle',
      destructive: 'text-data-down hover:bg-data-down-subtle',
    };

    const sizes = {
      sm: 'h-8 w-8 text-xs',
      md: 'h-9 w-9 text-sm',
      lg: 'h-11 w-11 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : (
          icon || children
        )}
      </button>
    );
  }
);

IconButton.displayName = 'IconButton';
