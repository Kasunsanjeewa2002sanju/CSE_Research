import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { marketStore, type LiveMarketSnapshot } from '@/stores/market-store';

// ============================================================================
// Mock EventSource Implementation for Stage 4 Testing
// ============================================================================

class MockEventSource {
  public url: string;
  public readyState: number = 0; // 0=CONNECTING, 1=OPEN, 2=CLOSED
  public listeners: Record<string, ((e: MessageEvent) => void)[]> = {};
  public onerror: ((e: Event) => void) | null = null;
  public onopen: ((e: Event) => void) | null = null;
  public static instances: MockEventSource[] = [];

  constructor(url: string) {
    this.url = url;
    this.readyState = 1;
    MockEventSource.instances.push(this);
  }

  public addEventListener(type: string, handler: (e: MessageEvent) => void) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(handler);
  }

  public removeEventListener(type: string, handler: (e: MessageEvent) => void) {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter((h) => h !== handler);
    }
  }

  public dispatch(type: string, eventData: unknown, lastEventId: string = '1') {
    const event = new MessageEvent(type, {
      data: JSON.stringify(eventData),
      lastEventId,
    });
    const handlers = this.listeners[type] || [];
    for (const handler of handlers) {
      handler(event);
    }
  }

  public triggerError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  public close() {
    this.readyState = 2;
  }
}

describe('Stage 4: Shared Live Market Store & EventSource Delivery', () => {
  const originalEventSource = globalThis.EventSource;
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.useFakeTimers();
    MockEventSource.instances = [];
    (globalThis as unknown as { EventSource: typeof MockEventSource }).EventSource = MockEventSource;
    marketStore.disconnect();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    marketStore.disconnect();
    globalThis.EventSource = originalEventSource;
    globalThis.fetch = originalFetch;
  });

  it('connects single EventSource on subscription and receives snapshot', () => {
    const listener = vi.fn();
    const unsubscribe = marketStore.subscribe(listener);

    expect(MockEventSource.instances.length).toBe(1);
    const mockES = MockEventSource.instances[0];
    expect(mockES.url).toContain('/market/stream');

    // Simulate incoming snapshot event
    const snapshotPayload: Partial<LiveMarketSnapshot> = {
      aspi_value: 22624.31,
      aspi_change: 177.58,
      aspi_percent_change: 0.79,
      aspi_previous_close: 22446.73,
      market_turnover: 9309760000.0,
      shares_traded: 245620000,
      total_trades: 15000,
      freshness: 'LIVE',
      source_timestamp: '2026-10-20T10:30:00Z',
    };

    mockES.dispatch('snapshot', snapshotPayload, '10');

    const state = marketStore.getState();
    expect(state.connection_status).toBe('LIVE');
    expect(state.derived_freshness_state).toBe('LIVE');
    expect(state.snapshot?.aspi_value).toBe(22624.31);
    expect(state.last_event_id).toBe('10');
    expect(state.seq).toBe(10);
    expect(listener).toHaveBeenCalled();

    unsubscribe();
  });

  it('merges tick diff without altering unmodified fields', () => {
    marketStore.subscribe(vi.fn());
    const mockES = MockEventSource.instances[0];

    // Seed snapshot
    mockES.dispatch(
      'snapshot',
      {
        aspi_value: 22624.31,
        aspi_change: 177.58,
        market_turnover: 9309760000.0,
        shares_traded: 245620000,
        total_trades: 15000,
        freshness: 'LIVE',
      },
      '1'
    );

    // Dispatch tick changing ONLY aspi_value
    mockES.dispatch(
      'tick',
      {
        aspi_value: 22650.0,
        aspi_change: 203.27,
      },
      '2'
    );

    const state = marketStore.getState();
    expect(state.snapshot?.aspi_value).toBe(22650.0);
    expect(state.snapshot?.aspi_change).toBe(203.27);
    // Unchanged fields must remain preserved
    expect(state.snapshot?.market_turnover).toBe(9309760000.0);
    expect(state.snapshot?.shares_traded).toBe(245620000);
    expect(state.last_event_id).toBe('2');
  });

  it('updates market status and derived freshness on status event', () => {
    marketStore.subscribe(vi.fn());
    const mockES = MockEventSource.instances[0];

    mockES.dispatch(
      'snapshot',
      {
        aspi_value: 22624.31,
        freshness: 'LIVE',
      },
      '1'
    );

    // Dispatch status event: market closed
    mockES.dispatch(
      'status',
      {
        freshness_state: 'CLOSED',
        market_status: { raw_status: 'Market Closed', status: 'Market Closed', is_open: false },
      },
      '2'
    );

    const state = marketStore.getState();
    expect(state.derived_freshness_state).toBe('CLOSED');
    expect(state.snapshot?.market_status?.is_open).toBe(false);
  });

  it('degrades to POLLING and triggers fallback when heartbeat times out after 30s', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        aspi_value: 22624.31,
        freshness_state: 'CLOSED',
        source_timestamp: '2026-10-20T11:00:00Z',
      }),
    });
    globalThis.fetch = mockFetch;

    marketStore.subscribe(vi.fn());
    const mockES = MockEventSource.instances[0];

    // Establish live snapshot
    mockES.dispatch('snapshot', { aspi_value: 22624.31, freshness: 'LIVE' }, '1');
    expect(marketStore.getState().connection_status).toBe('LIVE');

    // Fast forward 31 seconds without any heartbeat
    vi.advanceTimersByTime(31000);

    // Watchdog should have marked connection as degraded and started polling
    expect(marketStore.getState().connection_status).toBe('POLLING');
    expect(mockFetch).toHaveBeenCalled();
  });

  it('schedules reconnect with backoff when stream encounters network error', () => {
    marketStore.subscribe(vi.fn());
    const mockES = MockEventSource.instances[0];

    // Trigger error
    mockES.triggerError();

    expect(mockES.readyState).toBe(2); // closed
    expect(MockEventSource.instances.length).toBe(1);

    // Fast-forward reconnect timer (~1000ms with jitter)
    vi.advanceTimersByTime(1500);

    // A second EventSource should have been instantiated to reconnect
    expect(MockEventSource.instances.length).toBe(2);
  });

  it('pauses stream on document.hidden and resumes on visible', () => {
    marketStore.subscribe(vi.fn());
    const mockES = MockEventSource.instances[0];

    // Simulate tab backgrounding
    Object.defineProperty(document, 'hidden', { value: true, configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));

    expect(mockES.readyState).toBe(2); // closed/paused

    // Simulate tab foregrounding
    Object.defineProperty(document, 'hidden', { value: false, configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));

    // Reconnected
    expect(MockEventSource.instances.length).toBe(2);
  });
});
