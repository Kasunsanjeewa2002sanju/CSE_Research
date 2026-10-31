import { Outlet } from 'react-router-dom';
import { AlertTriangle, Clock } from 'lucide-react';
import { Header } from './Header';
import { Footer } from './Footer';
import { useMeta } from '@/context/MetaContext';

export function Shell() {
  const { connectionStatus, pipelineVersion, asOfDate, isStale } = useMeta();

  return (
    <div className="selection:bg-accent/20 flex min-h-screen flex-col bg-background text-text-primary transition-colors selection:text-text-primary">
      {/* Skip to main content link for WCAG keyboard accessibility */}
      <a
        href="#main-content"
        className="sr-only text-xs font-medium focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-button focus:bg-accent focus:px-4 focus:py-2 focus:text-accent-foreground focus:shadow-elevated focus:outline-none focus:ring-2 focus:ring-accent"
      >
        Skip to main content
      </a>

      {/* Staleness Banner (Honest UI - Rule FR5) */}
      {isStale && (
        <div
          role="alert"
          className="border-data-warning/30 border-b bg-data-warning-subtle px-4 py-2 font-sans text-xs font-medium text-data-warning"
        >
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-data-warning" />
              <span>
                <strong>Data Staleness Notice:</strong> Market telemetry and econometric pipeline
                results are currently flagged as stale. Latest verified data is as of{' '}
                <span className="font-mono font-semibold">{asOfDate || 'Unknown'}</span>.
              </span>
            </div>
            <div className="hidden items-center gap-1.5 text-[11px] text-text-muted sm:flex">
              <Clock className="h-3.5 w-3.5" />
              <span>Pipeline refresh pending</span>
            </div>
          </div>
        </div>
      )}

      {/* Top Navigation Shell (brand, all 10 module links, responsive drawer) */}
      <Header
        apiStatus={connectionStatus}
        pipelineVersion={pipelineVersion}
        asOfDate={asOfDate}
        isStale={isStale}
      />

      {/* Main Application Content Container */}
      <main id="main-content" className="flex flex-1 flex-col focus:outline-none" tabIndex={-1}>
        <Outlet />
      </main>

      {/* Shell Footer with telemetry, academic scope, and compliance */}
      <Footer
        apiStatus={connectionStatus}
        pipelineVersion={pipelineVersion}
        asOfDate={asOfDate}
        isStale={isStale}
      />
    </div>
  );
}
