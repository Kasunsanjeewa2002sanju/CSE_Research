import { ShieldCheck, Clock, Server } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface FooterProps {
  apiStatus?: 'online' | 'offline' | 'checking';
  asOfDate?: string | null;
  pipelineVersion?: string | null;
  isStale?: boolean;
}

export function Footer({
  apiStatus = 'checking',
  asOfDate = null,
  pipelineVersion = null,
  isStale = false,
}: FooterProps) {
  const statusLabel =
    apiStatus === 'online' ? 'API Online' : apiStatus === 'offline' ? 'API Offline' : 'Connecting';

  return (
    <footer
      className="bg-card/80 text-muted-foreground mt-auto border-t border-border px-4 py-4 text-xs backdrop-blur-sm transition-colors lg:px-8"
      role="contentinfo"
    >
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 md:flex-row">
        {/* Academic branding & research scope */}
        <div className="flex flex-col items-center gap-2 text-center sm:flex-row sm:items-start sm:text-left">
          <div className="text-foreground flex items-center gap-1.5 font-heading font-semibold">
            <span className="inline-block h-2 w-2 rounded-full bg-accent" />
            CSE ASPI Political Event Study
            
          </div>
          <span className="hidden text-border sm:inline">|</span>
          <span className="text-muted-foreground text-[11px]">
            University Econometric Research Platform • Sri Lankan Capital Markets
          </span>
        </div>

        {/* Live system telemetry & compliance status */}
        <div className="flex flex-wrap items-center justify-center gap-3 font-mono text-[11px] md:justify-end">
          {/* API Status badge */}
          <div
            className="bg-surface-muted/60 flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1"
            title="Backend API Connection Health (Wired via /system/status in F2)"
          >
            <Server className="text-muted-foreground h-3 w-3" aria-hidden="true" />
            <span>API:</span>
            <span className="inline-flex items-center gap-1">
              <span
                className={`h-1.5 w-1.5 rounded-full ${apiStatus === 'online' ? 'animate-pulse bg-data-up' : apiStatus === 'offline' ? 'bg-data-down' : 'animate-ping bg-amber-500'}`}
              />
              <span className="text-foreground font-medium">{statusLabel}</span>
            </span>
          </div>

          {/* Data-as-of timestamp */}
          {/* <div
            className="bg-surface-muted/60 flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1"
            title="Latest market date in econometric dataset (Asia/Colombo UTC+5:30)"
          >
            <Clock className="text-muted-foreground h-3 w-3" aria-hidden="true" />
            <span>Data As-Of:</span>
            <span className="text-foreground font-semibold">
              {asOfDate || 'Market Feed Active (F2)'}
            </span>
            {isStale && (
              <Badge variant="warning" size="sm" className="ml-1 px-1 py-0 text-[9px]">
                STALE
              </Badge>
            )}
          </div> */}

          {/* Pipeline version */}
          {pipelineVersion && (
            <div className="text-muted-foreground hidden items-center gap-1 lg:flex">
              <span>v{pipelineVersion}</span>
            </div>
          )}

          {/* Verification badge */}
          {/* <div
            className="text-muted-foreground hover:text-foreground flex cursor-help items-center gap-1 transition-colors"
            title="Strict zero-lookahead walk-forward enforcement & WCAG 2.1 AA accessibility"
          >
            <ShieldCheck className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
            <span className="hidden sm:inline">FR1–FR10 Verified</span>
          </div> */}
        </div>
      </div>
    </footer>
  );
}
