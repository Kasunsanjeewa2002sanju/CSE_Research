/**
 * Live Market Status Indicator (Stage 4).
 *
 * Displays real-time SSE stream status with color-coded states:
 * - LIVE: Emerald green with pulsating dot
 * - DELAYED: Amber warning
 * - CLOSED: Neutral slate
 * - STALE: Orange stale warning
 * - OFFLINE: Rose offline notice
 * - POLLING: Sky-blue degraded fallback
 *
 * Features:
 * - Accessible ARIA status announcements (role="status", aria-live="polite")
 * - Tooltip displaying the exact timestamp in Asia/Colombo timezone
 */

import { useMemo } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { useLiveMarket } from '@/stores/market-store';
import { cn } from '@/lib/utils';

export function MarketStatusIndicator({ className }: { className?: string }) {
  const connectionStatus = useLiveMarket((s) => s.connection_status);
  const freshnessState = useLiveMarket((s) => s.derived_freshness_state);
  const lastUpdated = useLiveMarket((s) => s.last_updated);

  // Derive unified presentation state
  const displayState = useMemo(() => {
    if (connectionStatus === 'OFFLINE') return 'OFFLINE';
    if (connectionStatus === 'CONNECTING' && !lastUpdated) return 'CONNECTING';
    if (connectionStatus === 'POLLING') return 'POLLING';
    return freshnessState || 'CLOSED';
  }, [connectionStatus, freshnessState, lastUpdated]);

  // Format timestamp strictly in Asia/Colombo timezone
  const formattedColomboTime = useMemo(() => {
    if (!lastUpdated) return 'Awaiting initial snapshot';
    try {
      const d = new Date(lastUpdated);
      return (
        new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Asia/Colombo',
          year: 'numeric',
          month: 'short',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        }).format(d) + ' Asia/Colombo'
      );
    } catch {
      return String(lastUpdated);
    }
  }, [lastUpdated]);

  // Color & Badge configuration
  const config = useMemo(() => {
    switch (displayState) {
      case 'LIVE':
        return {
          textColor: 'text-emerald-400',
          dotColor: 'bg-emerald-400',
          pulseColor: 'bg-emerald-400',
          hasPulse: true,
          label: 'LIVE',
          description: 'Streaming real-time ticks from Colombo Stock Exchange',
        };
      case 'DELAYED':
        return {
          textColor: 'text-amber-400',
          dotColor: 'bg-amber-400',
          pulseColor: 'bg-amber-400',
          hasPulse: false,
          label: 'DELAYED',
          description: 'Active session with delayed feed (> 60s)',
        };
      case 'CLOSED':
        return {
          textColor: 'text-slate-300',
          dotColor: 'bg-slate-400',
          pulseColor: '',
          hasPulse: false,
          label: 'CLOSED',
          description: 'CSE session closed; showing official closing print',
        };
      case 'STALE':
        return {
          textColor: 'text-orange-400',
          dotColor: 'bg-orange-400',
          pulseColor: '',
          hasPulse: false,
          label: 'STALE',
          description: 'Market data feed stale; refreshing',
        };
      case 'POLLING':
        return {
          textColor: 'text-sky-400',
          dotColor: 'bg-sky-400',
          pulseColor: 'bg-sky-400',
          hasPulse: true,
          label: 'POLLING',
          description: 'Stream degraded; active polling fallback (5s cadence)',
        };
      case 'OFFLINE':
      default:
        return {
          textColor: 'text-rose-400',
          dotColor: 'bg-rose-400',
          pulseColor: '',
          hasPulse: false,
          label: 'OFFLINE',
          description: 'Market stream and polling disconnected',
        };
    }
  }, [displayState]);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Market Feed: ${config.label}. Last updated: ${formattedColomboTime}`}
      title={`Market Data Feed: ${config.label}\n${config.description}\nLast update: ${formattedColomboTime}`}
      className={cn(
        'group relative inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 font-mono text-[11px] font-semibold tracking-wide transition-colors hover:bg-white/10 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent',
        config.textColor,
        className
      )}
    >
      {/* Icon or Status Indicator Dot */}
      {displayState === 'OFFLINE' ? (
        <WifiOff className="h-3 w-3 shrink-0 text-rose-400" aria-hidden="true" />
      ) : displayState === 'POLLING' ? (
        <RefreshCw className="h-3 w-3 shrink-0 animate-spin text-sky-400" aria-hidden="true" />
      ) : (
        <span className="relative flex h-2 w-2 shrink-0 items-center justify-center">
          {config.hasPulse && (
            <span
              className={cn(
                'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
                config.pulseColor
              )}
            />
          )}
          <span className={cn('relative inline-flex h-1.5 w-1.5 rounded-full', config.dotColor)} />
        </span>
      )}

      {/* State Text Label */}
      <span className="select-none">{config.label}</span>

      {/* Accessible Screen-Reader Announcement */}
      <span className="sr-only">
        {config.label} - Last updated at {formattedColomboTime}
      </span>
    </div>
  );
}
