import React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'danger' | 'navy';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  icon?: React.ReactNode;
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      icon,
      asChild = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium font-sans rounded-button transition-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none';

    const normalizedVariant = variant === 'danger' ? 'destructive' : variant;

    const variants = {
      // Primary uses the 10% Cyan Accent (#00B8D9) with deep contrast text (#0B1B33, 8.5:1 contrast)
      primary:
        'bg-accent text-accent-foreground font-semibold hover:bg-accent-hover shadow-soft active:translate-y-px',
      // Secondary uses cool neutral blue tint
      secondary:
        'bg-blue-ice text-blue-navy hover:bg-blue-soft/50 dark:bg-blue-soft/30 dark:text-text-primary',
      // Outline has subtle border and hover surface
      outline:
        'border border-border bg-surface-white text-text-primary hover:bg-surface-subtle hover:border-border-strong',
      // Ghost has transparent background
      ghost: 'text-text-primary hover:bg-surface-subtle hover:text-text-primary',
      // Destructive uses semantic data down
      destructive: 'bg-data-down text-white hover:bg-data-down/90 shadow-soft',
      // Navy uses institutional blue
      navy: 'bg-blue-navy text-white hover:bg-blue-cobalt shadow-soft',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs gap-1.5',
      md: 'h-9 px-4 text-sm gap-2',
      lg: 'h-11 px-6 text-base gap-2.5',
    };

    const effectiveLeftIcon = leftIcon || icon;
    const computedClassName = cn(baseStyles, variants[normalizedVariant], sizes[size], className);

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{
        className?: string;
        children?: React.ReactNode;
      }>;
      return React.cloneElement(child, {
        className: cn(computedClassName, child.props.className),
        children: (
          <>
            {effectiveLeftIcon && <span className="shrink-0">{effectiveLeftIcon}</span>}
            {child.props.children}
            {rightIcon && <span className="shrink-0">{rightIcon}</span>}
          </>
        ),
      });
    }

    return (
      <button ref={ref} className={computedClassName} disabled={disabled || isLoading} {...props}>
        {isLoading ? (
          <svg
            className="h-4 w-4 animate-spin text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        ) : (
          effectiveLeftIcon && <span className="shrink-0">{effectiveLeftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
