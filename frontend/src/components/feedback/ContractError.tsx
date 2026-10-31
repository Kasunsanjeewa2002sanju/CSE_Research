import { useState } from 'react';
import { ChevronDown, ChevronRight, FileWarning } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export interface ContractErrorProps {
  endpoint: string;
  error: Error & {
    zodError?: { issues: Array<{ path: (string | number)[]; message: string }> };
    rawPayload?: unknown;
  };
  onRetry?: () => void;
}

export function ContractError({ endpoint, error, onRetry }: ContractErrorProps) {
  const [showDetails, setShowDetails] = useState(false);
  const issues = error.zodError?.issues || [];

  return (
    <div
      role="alert"
      className="border-destructive/40 bg-destructive/10 text-foreground space-y-4 rounded-lg border p-5"
    >
      <div className="flex items-start gap-3">
        <FileWarning className="text-destructive mt-0.5 h-6 w-6 shrink-0" aria-hidden="true" />
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <span className="bg-destructive text-destructive-foreground rounded px-2 py-0.5 font-mono text-xs font-bold uppercase tracking-wider">
              Rule FR4: Contract Error
            </span>
            <span className="text-muted-foreground font-mono text-xs">{endpoint}</span>
          </div>
          <h4 className="text-destructive font-heading text-base font-semibold">
            API Schema Validation Mismatch
          </h4>
          <p className="text-muted-foreground text-sm leading-relaxed">
            The response received from the backend does not conform to the expected OpenAPI schema
            specification. Silent fallbacks are strictly prohibited by Rule FR4.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-1">
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Retry Request
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowDetails(!showDetails)}
          className="text-muted-foreground hover:text-foreground text-xs"
        >
          {showDetails ? (
            <ChevronDown className="mr-1 h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="mr-1 h-3.5 w-3.5" />
          )}
          {showDetails ? 'Hide Contract Diagnostics' : 'Inspect Zod Schema Issues'}
        </Button>
      </div>

      {showDetails && (
        <div className="bg-background/80 mt-3 space-y-2 overflow-x-auto rounded border border-border p-3 font-mono text-xs">
          <div className="text-muted-foreground font-semibold">
            Validation Issues ({issues.length}):
          </div>
          {issues.length > 0 ? (
            <ul className="text-destructive list-inside list-disc space-y-1">
              {issues.map((issue, idx) => (
                <li key={idx}>
                  <span className="text-foreground">
                    {issue.path.length > 0 ? issue.path.join('.') : 'root'}:
                  </span>{' '}
                  {issue.message}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-muted-foreground">{error.message}</div>
          )}

          {error.rawPayload !== undefined && (
            <details className="pt-2">
              <summary className="text-muted-foreground hover:text-foreground cursor-pointer">
                Raw Payload Preview
              </summary>
              <pre className="bg-muted/40 mt-2 max-h-48 overflow-y-auto rounded p-2 text-[11px]">
                {JSON.stringify(error.rawPayload, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
