import React from 'react';
import { Database, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  title?: string;
  message?: string;
  description?: string;
  gapId?: string;
  gapMessage?: string;
  icon?: React.ReactNode | React.ElementType;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = 'Data Not Available from Backend',
  message,
  description,
  gapId,
  gapMessage,
  icon,
  action,
  className,
}: EmptyStateProps) {
  const displayMessage =
    description ||
    message ||
    'This data point or module is pending backend pipeline exposure. Gaps are formally documented per Rule FR9.';

  // Handle icon whether passed as a JSX Element, Lucide Component, or empty
  let renderIcon: React.ReactNode = <Database className="h-5 w-5" aria-hidden="true" />;
  if (icon) {
    if (React.isValidElement(icon)) {
      renderIcon = icon;
    } else if (typeof icon === 'function' || typeof icon === 'object') {
      const IconComponent = icon as React.ElementType;
      renderIcon = <IconComponent className="h-5 w-5" aria-hidden="true" />;
    }
  }

  return (
    <div
      className={cn(
        'bg-surface-subtle/40 space-y-3 rounded-card border border-dashed border-border p-8 text-center',
        className
      )}
    >
      <div className="dark:bg-blue-soft/30 mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-blue-ice text-blue-navy dark:text-blue-vibrant">
        {renderIcon}
      </div>

      <div className="space-y-1">
        <h4 className="font-heading text-sm font-semibold text-text-primary">{title}</h4>
        <p className="mx-auto max-w-md text-xs leading-relaxed text-text-muted">{displayMessage}</p>
      </div>

      {(gapId || gapMessage) && (
        <div className="pt-1">
          <span className="bg-accent/15 border-accent/30 inline-flex items-center gap-1.5 rounded-chip border px-2.5 py-1 font-mono text-[11px] font-medium text-accent-hover dark:text-accent">
            <span>{gapId ? `Registered Gap: ${gapId}` : gapMessage}</span>
            <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      )}

      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
