import { Database, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  title?: string;
  message?: string;
  gapId?: string;
  className?: string;
}

export function EmptyState({
  title = 'Data Not Available from Backend',
  message = 'This data point or module is pending backend pipeline exposure. Gaps are formally documented per Rule FR9.',
  gapId,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'bg-muted/20 space-y-3 rounded-lg border border-dashed border-border p-8 text-center',
        className
      )}
    >
      <div className="bg-muted text-muted-foreground mx-auto flex h-10 w-10 items-center justify-center rounded-full">
        <Database className="h-5 w-5" aria-hidden="true" />
      </div>

      <div className="space-y-1">
        <h4 className="text-foreground font-heading text-sm font-medium">{title}</h4>
        <p className="text-muted-foreground mx-auto max-w-md text-xs leading-relaxed">{message}</p>
      </div>

      {gapId && (
        <div className="pt-1">
          <span className="text-primary bg-primary/10 inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[11px]">
            <span>Registered Gap: {gapId}</span>
            <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      )}
    </div>
  );
}
