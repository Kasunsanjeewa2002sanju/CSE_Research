import { ServerOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { getApiBaseUrl } from '@/lib/env';

export interface BackendUnavailableProps {
  endpoint?: string;
  onRetry?: () => void;
  message?: string;
}

export function BackendUnavailable({ endpoint, onRetry, message }: BackendUnavailableProps) {
  const baseUrl = getApiBaseUrl();

  return (
    <div
      role="alert"
      className="bg-card mx-auto my-8 max-w-lg space-y-4 rounded-lg border border-border p-8 text-center shadow-sm"
    >
      <div className="bg-muted/60 text-muted-foreground mx-auto flex h-14 w-14 items-center justify-center rounded-full">
        <ServerOff className="h-7 w-7" aria-hidden="true" />
      </div>

      <div className="space-y-2">
        <div className="bg-secondary text-secondary-foreground inline-block rounded px-2.5 py-0.5 font-mono text-xs font-medium">
          Rule FR3: No Mock Fallback
        </div>
        <h3 className="font-heading text-lg font-semibold tracking-tight">
          Backend Service Offline
        </h3>
        <p className="text-muted-foreground text-sm leading-relaxed">
          {message ||
            'The CSE Research API service is currently unreachable. Mock data in production source code is strictly prohibited by Rule FR3.'}
        </p>
      </div>

      <div className="bg-muted/40 text-muted-foreground space-y-1 rounded-md border border-border p-3 text-left font-mono text-xs">
        <div>
          <span className="text-foreground font-semibold">Target URL:</span> {baseUrl}
        </div>
        {endpoint && (
          <div>
            <span className="text-foreground font-semibold">Endpoint:</span> {endpoint}
          </div>
        )}
      </div>

      {onRetry && (
        <div className="pt-2">
          <Button variant="primary" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw className="h-3.5 w-3.5" />
            Reconnect to Backend
          </Button>
        </div>
      )}
    </div>
  );
}
