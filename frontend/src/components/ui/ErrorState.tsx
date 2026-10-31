import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Failed to Load Data',
  message = 'An unexpected error occurred while communicating with the backend research service.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'border-data-down/30 bg-data-down-subtle/50 space-y-3 rounded-card border p-6 text-center sm:p-8',
        className
      )}
    >
      <div className="bg-data-down/15 mx-auto flex h-12 w-12 items-center justify-center rounded-full text-data-down">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
      </div>

      <div className="space-y-1">
        <h4 className="font-heading text-base font-bold text-text-primary">{title}</h4>
        <p className="mx-auto max-w-md text-xs leading-relaxed text-text-muted">{message}</p>
      </div>

      {onRetry && (
        <div className="pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
}
