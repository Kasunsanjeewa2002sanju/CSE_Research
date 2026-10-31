/**
 * Shared Real-Time Market Data Store & Service (Stage 4).
 *
 * Architecture:
 * - Single shared EventSource per tab across all components
 * - Event types: "snapshot", "tick", "status", "heartbeat", "error"
 * - Reconnect with exponential backoff + random jitter
 * - Heartbeat watchdog (2x interval = 30s) -> degraded connection -> polling fallback
 * - Tab visibility (document.hidden) pause & resume with fresh snapshot
 * - Selector API via useSyncExternalStore (subscribes only to requested fields)
 * - Zero hardcoded URLs (driven strictly by getApiBaseUrl() from env)
 */

import { useSyncExternalStore, useRef, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/env';

export type ConnectionStatus = 'CONNECTING' | 'LIVE' | 'POLLING' | 'OFFLINE';
export type FreshnessState = 'LIVE' | 'DELAYED' | 'CLOSED' | 'STALE' | 'OFFLINE';

export interface MarketStatus {
  raw_status: string;
  status: string;
  is_open: boolean;
  timestamp?: string;
  message?: string | null;
}

export interface LiveMarketSnapshot {
  aspi_value: number;
  aspi_change: number;
  aspi_percent_change: number;
  aspi_previous_close: number;
  sp20_value?: number | null;
  sp20_change?: number | null;
  sp20_percent_change?: number | null;
  sp20_previous_close?: number | null;
  market_turnover: number;
  shares_traded: number;
  total_trades: number;
  market_status?: MarketStatus;
  freshness?: FreshnessState;
  source_timestamp?: string;
  source?: string;
  [key: string]: unknown;
}

export interface LiveMarketState {
  snapshot: LiveMarketSnapshot | null;
  derived_freshness_state: FreshnessState;
  last_updated: string | null;
  connection_status: ConnectionStatus;
  last_event_id: string | null;
  seq: number;
  error: string | null;
  sparklines: {
    aspi: number[];
    sp20: number[];
    turnover: number[];
    shares: number[];
  };
}

const HEARTBEAT_TIMEOUT_MS = 30000; // 2x server heartbeat interval (15s)
const POLLING_INTERVAL_MS = 1000; // 1-second real-time polling
const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30000;

class MarketStore {
  private state: LiveMarketState = {
    snapshot: null,
    derived_freshness_state: 'CLOSED',
    last_updated: null,
    connection_status: 'CONNECTING',
    last_event_id: null,
    seq: 0,
    error: null,
    sparklines: {
      aspi: [],
      sp20: [],
      turnover: [],
      shares: [],
    },
  };

  private listeners: Set<() => void> = new Set();
  private eventSource: EventSource | null = null;
  private heartbeatTimer: ReturnType<typeof setTimeout> | null = null;
  private pollingTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private isPaused = false;
  private subscriberCount = 0;

  constructor() {
    this.initVisibilityListener();
  }

  public getState(): LiveMarketState {
    return this.state;
  }

  public seedSparklines(seeds: {
    aspi?: number[];
    sp20?: number[];
    turnover?: number[];
    shares?: number[];
  }): void {
    let changed = false;
    const next = { ...this.state.sparklines };
    if (seeds.aspi && seeds.aspi.length > 0 && next.aspi.length <= 1) {
      next.aspi = seeds.aspi.slice(-30);
      changed = true;
    }
    if (seeds.sp20 && seeds.sp20.length > 0 && next.sp20.length <= 1) {
      next.sp20 = seeds.sp20.slice(-30);
      changed = true;
    }
    if (seeds.turnover && seeds.turnover.length > 0 && next.turnover.length <= 1) {
      next.turnover = seeds.turnover.slice(-30);
      changed = true;
    }
    if (seeds.shares && seeds.shares.length > 0 && next.shares.length <= 1) {
      next.shares = seeds.shares.slice(-30);
      changed = true;
    }
    if (changed) {
      this.setState({ sparklines: next });
    }
  }

  public subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    this.subscriberCount++;

    if (!this.eventSource && !this.isPaused) {
      this.connect();
    }

    return () => {
      this.listeners.delete(listener);
      this.subscriberCount--;
      if (this.subscriberCount <= 0) {
        // Optional grace cleanup
      }
    };
  };

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  private setState(partial: Partial<LiveMarketState>): void {
    this.state = { ...this.state, ...partial };
    this.notify();
  }

  private getStreamUrl(): string {
    const base = getApiBaseUrl().replace(/\/+$/, '');
    const url = new URL(`${base}/market/stream`);
    if (this.state.last_event_id) {
      url.searchParams.set('last_event_id', this.state.last_event_id);
    }
    return url.toString();
  }

  private getLatestUrl(): string {
    const base = getApiBaseUrl().replace(/\/+$/, '');
    return `${base}/market/latest`;
  }

  public connect(): void {
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      return;
    }

    if (this.isPaused) {
      return;
    }

    // Clean up existing EventSource if active
    if (this.eventSource) {
      try {
        this.eventSource.close();
      } catch {
        // ignore
      }
      this.eventSource = null;
    }

    const streamUrl = this.getStreamUrl();
    try {
      this.setState({ connection_status: this.state.snapshot ? this.state.connection_status : 'CONNECTING' });
      const es = new EventSource(streamUrl);
      this.eventSource = es;

      es.addEventListener('snapshot', this.handleSnapshotEvent);
      es.addEventListener('tick', this.handleTickEvent);
      es.addEventListener('status', this.handleStatusEvent);
      es.addEventListener('heartbeat', this.handleHeartbeatEvent);
      es.addEventListener('error', this.handleErrorEvent);

      es.onerror = this.handleEventSourceError;

      this.resetHeartbeatWatchdog();
    } catch (err) {
      console.warn('[MarketStore] Failed to initialize EventSource:', err);
      this.handleEventSourceError();
    }
  }

  public disconnect(): void {
    this.clearTimers();
    this.reconnectAttempts = 0;
    if (this.eventSource) {
      try {
        this.eventSource.close();
      } catch {
        // ignore
      }
      this.eventSource = null;
    }
  }

  private clearTimers(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
  }

  private resetHeartbeatWatchdog(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
    }

    this.heartbeatTimer = setTimeout(() => {
      this.handleHeartbeatTimeout();
    }, HEARTBEAT_TIMEOUT_MS);
  }

  private handleHeartbeatTimeout(): void {
    console.warn('[MarketStore] No heartbeat for 30s (2x interval). Connection degraded, falling back to polling.');
    
    // Fall back to polling
    this.setState({ connection_status: 'POLLING' });
    this.startPollingFallback();
    
    // Attempt reconnecting stream in background
    this.scheduleReconnect();
  }

  private handleSnapshotEvent = (e: MessageEvent): void => {
    try {
      const data: LiveMarketSnapshot = JSON.parse(e.data);
      const seq = e.lastEventId ? parseInt(e.lastEventId, 10) : (this.state.seq + 1);

      this.reconnectAttempts = 0;
      this.stopPollingFallback();
      this.resetHeartbeatWatchdog();

      const freshness = data.freshness || (data.freshness_state as FreshnessState) || 'CLOSED';
      const updated = data.source_timestamp || new Date().toISOString();

      const nextSparklines = { ...this.state.sparklines };
      if (typeof data.aspi_value === 'number' && nextSparklines.aspi.length === 0) {
        nextSparklines.aspi = [data.aspi_value];
      }
      if (typeof data.sp20_value === 'number' && nextSparklines.sp20.length === 0) {
        nextSparklines.sp20 = [data.sp20_value];
      }
      if (typeof data.market_turnover === 'number' && nextSparklines.turnover.length === 0) {
        nextSparklines.turnover = [data.market_turnover];
      }
      if (typeof data.shares_traded === 'number' && nextSparklines.shares.length === 0) {
        nextSparklines.shares = [data.shares_traded];
      }

      this.setState({
        snapshot: data,
        derived_freshness_state: freshness,
        last_updated: updated,
        connection_status: 'LIVE',
        last_event_id: e.lastEventId || this.state.last_event_id,
        seq: isNaN(seq) ? this.state.seq : seq,
        error: null,
        sparklines: nextSparklines,
      });
    } catch (err) {
      console.error('[MarketStore] Error parsing snapshot event:', err);
    }
  };

  private handleTickEvent = (e: MessageEvent): void => {
    try {
      const diff = JSON.parse(e.data);
      const seq = e.lastEventId ? parseInt(e.lastEventId, 10) : (this.state.seq + 1);

      this.resetHeartbeatWatchdog();

      const updatedSnapshot: LiveMarketSnapshot = this.state.snapshot
        ? { ...this.state.snapshot, ...diff }
        : (diff as LiveMarketSnapshot);

      const updated = diff.source_timestamp || updatedSnapshot.source_timestamp || new Date().toISOString();

      const nextSparklines = { ...this.state.sparklines };
      if (typeof diff.aspi_value === 'number') {
        nextSparklines.aspi = [...nextSparklines.aspi, diff.aspi_value].slice(-30);
      }
      if (typeof diff.sp20_value === 'number') {
        nextSparklines.sp20 = [...nextSparklines.sp20, diff.sp20_value].slice(-30);
      }
      if (typeof diff.market_turnover === 'number') {
        nextSparklines.turnover = [...nextSparklines.turnover, diff.market_turnover].slice(-30);
      }
      if (typeof diff.shares_traded === 'number') {
        nextSparklines.shares = [...nextSparklines.shares, diff.shares_traded].slice(-30);
      }

      this.setState({
        snapshot: updatedSnapshot,
        last_updated: updated,
        connection_status: 'LIVE',
        last_event_id: e.lastEventId || this.state.last_event_id,
        seq: isNaN(seq) ? this.state.seq : seq,
        error: null,
        sparklines: nextSparklines,
      });
    } catch (err) {
      console.error('[MarketStore] Error parsing tick event:', err);
    }
  };

  private handleStatusEvent = (e: MessageEvent): void => {
    try {
      const payload = JSON.parse(e.data);
      this.resetHeartbeatWatchdog();

      const newFreshness: FreshnessState =
        payload.freshness_state ||
        payload.freshness ||
        this.state.derived_freshness_state;

      const updatedSnapshot: LiveMarketSnapshot | null = this.state.snapshot
        ? {
            ...this.state.snapshot,
            market_status: payload.market_status || this.state.snapshot.market_status,
            freshness: newFreshness,
          }
        : null;

      const updated = payload.source_timestamp || this.state.last_updated;

      this.setState({
        snapshot: updatedSnapshot,
        derived_freshness_state: newFreshness,
        last_updated: updated,
        last_event_id: e.lastEventId || this.state.last_event_id,
        connection_status: 'LIVE',
      });
    } catch (err) {
      console.error('[MarketStore] Error parsing status event:', err);
    }
  };

  private handleHeartbeatEvent = (_e: MessageEvent): void => {
    // Heartbeat received -> connection is healthy!
    this.resetHeartbeatWatchdog();
    if (this.state.connection_status === 'POLLING' || this.state.connection_status === 'CONNECTING') {
      this.setState({ connection_status: 'LIVE' });
      this.stopPollingFallback();
    }
  };

  private handleErrorEvent = (e: MessageEvent): void => {
    try {
      const errData = JSON.parse(e.data);
      console.warn('[MarketStore] Stream server non-fatal error:', errData);
    } catch {
      // non-json error
    }
  };

  private handleEventSourceError = (): void => {
    if (this.eventSource) {
      try {
        this.eventSource.close();
      } catch {
        // ignore
      }
      this.eventSource = null;
    }

    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    // Immediately start polling fallback so data remains available
    this.setState({
      connection_status: this.state.snapshot ? 'POLLING' : 'CONNECTING',
    });
    this.startPollingFallback();

    // Schedule reconnect with exponential backoff + jitter
    this.scheduleReconnect();
  };

  private scheduleReconnect(): void {
    if (this.reconnectTimer || this.isPaused) {
      return;
    }

    this.reconnectAttempts++;
    // Exponential backoff: base * 1.5^attempts
    const exponentialDelay = Math.min(
      MAX_BACKOFF_MS,
      INITIAL_BACKOFF_MS * Math.pow(1.5, this.reconnectAttempts - 1)
    );
    // Jitter: +/- 20%
    const jitter = 0.8 + Math.random() * 0.4;
    const delay = Math.round(exponentialDelay * jitter);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private startPollingFallback(): void {
    // Trigger immediate poll
    this.pollLatest();

    if (!this.pollingTimer) {
      this.pollingTimer = setInterval(() => {
        this.pollLatest();
      }, POLLING_INTERVAL_MS);
    }
  }

  private stopPollingFallback(): void {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
  }

  public async pollLatest(): Promise<void> {
    try {
      const url = `${this.getLatestUrl()}?_t=${Date.now()}`;
      const resp = await fetch(url, {
        headers: { Accept: 'application/json', 'Cache-Control': 'no-cache' },
        cache: 'no-store',
      });
      if (!resp.ok) {
        throw new Error(`Polling HTTP ${resp.status}`);
      }
      const data = await resp.json();
      const freshness: FreshnessState = data.freshness_state || data.freshness || 'CLOSED';
      const isLive = freshness === 'LIVE' || data.market_status?.is_open || data.market_status?.status === 'Regular Trading';
      const nowIso = new Date().toISOString();
      const updated = isLive ? nowIso : (data.source_timestamp || nowIso);

      const mergedSnapshot: LiveMarketSnapshot = {
        ...(this.state.snapshot || {}),
        ...data,
      };

      const nextSparklines = { ...this.state.sparklines };
      if (typeof data.aspi_value === 'number') {
        const lastAspi = nextSparklines.aspi[nextSparklines.aspi.length - 1];
        if (lastAspi !== data.aspi_value) {
          nextSparklines.aspi = [...nextSparklines.aspi, data.aspi_value].slice(-30);
        }
      }
      if (typeof data.sp20_value === 'number') {
        const lastSp = nextSparklines.sp20[nextSparklines.sp20.length - 1];
        if (lastSp !== data.sp20_value) {
          nextSparklines.sp20 = [...nextSparklines.sp20, data.sp20_value].slice(-30);
        }
      }
      if (typeof data.market_turnover === 'number') {
        const lastTurnover = nextSparklines.turnover[nextSparklines.turnover.length - 1];
        if (lastTurnover !== data.market_turnover) {
          nextSparklines.turnover = [...nextSparklines.turnover, data.market_turnover].slice(-30);
        }
      }
      if (typeof data.shares_traded === 'number') {
        const lastShares = nextSparklines.shares[nextSparklines.shares.length - 1];
        if (lastShares !== data.shares_traded) {
          nextSparklines.shares = [...nextSparklines.shares, data.shares_traded].slice(-30);
        }
      }

      this.setState({
        snapshot: mergedSnapshot,
        derived_freshness_state: freshness,
        last_updated: updated,
        connection_status: this.state.connection_status === 'CONNECTING' ? 'POLLING' : this.state.connection_status,
        sparklines: nextSparklines,
        error: null,
      });

    } catch (err) {
      // If both SSE is down and polling failed, mark OFFLINE
      if (!this.eventSource) {
        this.setState({
          connection_status: 'OFFLINE',
          derived_freshness_state: 'OFFLINE',
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  }

  private initVisibilityListener(): void {
    if (typeof document === 'undefined') {
      return;
    }

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Tab backgrounded -> pause stream to conserve network/server resources
        this.isPaused = true;
        this.disconnect();
      } else {
        // Tab foregrounded -> resume stream with fresh snapshot
        this.isPaused = false;
        this.connect();
        // Immediately fetch latest to avoid stale data while connecting
        this.pollLatest();
      }
    });
  }
}

// Global shared store singleton per browser tab
export const marketStore = new MarketStore();
if (typeof window !== 'undefined') {
  (window as unknown as { __marketStore: MarketStore }).__marketStore = marketStore;
}

function shallowEqual<T>(a: T, b: T): boolean {
  if (Object.is(a, b)) return true;
  if (typeof a !== 'object' || a === null || typeof b !== 'object' || b === null) {
    return false;
  }
  const keysA = Object.keys(a) as (keyof T)[];
  const keysB = Object.keys(b) as (keyof T)[];
  if (keysA.length !== keysB.length) return false;
  for (let i = 0; i < keysA.length; i++) {
    const key = keysA[i];
    if (!Object.prototype.hasOwnProperty.call(b, key) || !Object.is(a[key], b[key])) {
      return false;
    }
  }
  return true;
}

/**
 * React hook subscribing to live market state or a derived slice.
 *
 * Employs React 18 useSyncExternalStore with shallow-equal memoization
 * to ensure components ONLY re-render when their selected slice actually changes
 * (prevents whole-page re-renders on every tick and guarantees zero wasted cycles).
 */
export function useLiveMarket<T = LiveMarketState>(
  selector: (state: LiveMarketState) => T = (s) => s as unknown as T
): T {
  const lastSelectedStateRef = useRef<T>();
  const lastStateRef = useRef<LiveMarketState>();

  const getSnapshot = useCallback(() => {
    const currentState = marketStore.getState();
    if (lastStateRef.current === currentState && lastSelectedStateRef.current !== undefined) {
      return lastSelectedStateRef.current;
    }
    const nextSelected = selector(currentState);
    if (
      lastSelectedStateRef.current !== undefined &&
      shallowEqual(lastSelectedStateRef.current, nextSelected)
    ) {
      lastStateRef.current = currentState;
      return lastSelectedStateRef.current;
    }
    lastStateRef.current = currentState;
    lastSelectedStateRef.current = nextSelected;
    return nextSelected;
  }, [selector]);

  return useSyncExternalStore(
    marketStore.subscribe,
    getSnapshot,
    getSnapshot
  );
}

/**
 * Imperative accessor for components/tests that need current snapshot without subscribing.
 */
export function getLiveMarketSnapshot(): LiveMarketState {
  return marketStore.getState();
}
