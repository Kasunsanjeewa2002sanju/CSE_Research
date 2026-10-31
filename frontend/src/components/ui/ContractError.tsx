import { useState } from 'react';
import { ChevronDown, ChevronRight, FileWarning } from 'lucide-react';
import { Button } from './Button';

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
      className="border-data-down/40 bg-data-down-subtle/40 space-y-4 rounded-card border p-5 text-text-primary sm:p-6"
    >
      <div className="flex items-start gap-3">
        <FileWarning className="mt-0.5 h-6 w-6 shrink-0 text-data-down" aria-hidden="true" />
        <div className="flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-chip bg-data-down px-2 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wider text-white">
              Rule FR4: Contract Error
            </span>
            <span className="font-mono text-xs text-text-muted">{endpoint}</span>
          </div>
          <h4 className="font-heading text-base font-bold text-data-down">
            API Boundary Validation Mismatch
          </h4>
          <p className="text-xs leading-relaxed text-text-muted">
            The response received from the backend does not conform to the expected schema contract.
            Per Rule FR4, silent fallbacks are prohibited.
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
          className="text-xs text-text-muted hover:text-text-primary"
        >
          {showDetails ? (
            <ChevronDown className="mr-1 h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="mr-1 h-3.5 w-3.5" />
          )}
          {showDetails ? 'Hide Diagnostics' : 'Inspect Zod Schema Issues'}
        </Button>
      </div>

      {showDetails && (
        <div className="mt-3 space-y-2 overflow-x-auto rounded-button border border-border bg-surface-white p-3 font-mono text-xs">
          <div className="font-semibold text-text-muted">Validation Issues ({issues.length}):</div>
          {issues.length > 0 ? (
            <ul className="list-inside list-disc space-y-1 text-data-down">
              {issues.map((issue, idx) => (
                <li key={idx}>
                  <span className="font-bold text-text-primary">
                    {issue.path.length > 0 ? issue.path.join('.') : 'root'}:
                  </span>{' '}
                  {issue.message}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-text-muted">{error.message}</div>
          )}

          {error.rawPayload !== undefined && (
            <details className="pt-2">
              <summary className="cursor-pointer text-text-muted hover:text-text-primary">
                Raw Payload Preview
              </summary>
              <pre className="border-border/60 mt-2 max-h-48 overflow-y-auto rounded border bg-surface-subtle p-2 text-[11px]">
                {JSON.stringify(error.rawPayload, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
