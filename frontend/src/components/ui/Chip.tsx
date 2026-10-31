import React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  onRemove?: (e: React.MouseEvent) => void;
  icon?: React.ReactNode;
  label?: string;
}

export function Chip({
  className,
  active = false,
  onRemove,
  icon,
  label,
  children,
  onClick,
  ...props
}: ChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'transition-standard inline-flex select-none items-center gap-1.5 rounded-chip border px-3 py-1 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        active
          ? 'border-blue-navy bg-blue-navy text-white shadow-soft'
          : 'border-border bg-surface-white text-text-primary hover:border-border-strong hover:bg-surface-subtle',
        className
      )}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label || children}</span>
      {onRemove && (
        <span
          role="button"
          tabIndex={0}
          aria-label="Remove filter"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(e);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.stopPropagation();
              onRemove(e as unknown as React.MouseEvent);
            }
          }}
          className="transition-standard -mr-1 ml-0.5 cursor-pointer rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/10"
        >
          <X className="h-3 w-3" />
        </span>
      )}
    </button>
  );
}
