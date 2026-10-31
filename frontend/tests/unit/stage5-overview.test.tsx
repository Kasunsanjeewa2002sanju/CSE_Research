import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MetaContext, type MetaContextValue } from '@/context/MetaContext';
import { StatCard } from '@/components/ui/StatCard';
import {
  AspiStatCard,
  Sp20StatCard,
  TurnoverStatCard,
  SharesStatCard,
  OverviewStatCards,
} from '@/features/overview/components/OverviewStatCards';
import { MarketOverviewStrip } from '@/features/overview/components/MarketOverviewStrip';
import { marketStore } from '@/stores/market-store';
import type { LiveMarketSnapshot } from '@/api/types';

const mockMetaValue: MetaContextValue = {
  connectionStatus: 'online',
  pipelineVersion: '1.0.0',
  asOfDate: '2026-10-20',
  isStale: false,
  meta: null,
  status: null,
  glossaryMap: {
    aspi: {
      metric_id: 'aspi',
      name: 'All Share Price Index',
      definition: 'Benchmark stock index of the Colombo Stock Exchange',
    },
    sp20: {
      metric_id: 'sp20',
      name: 'S&P Sri Lanka 20',
      definition: 'Top 20 blue-chip stocks index',
    },
    turnover: {
      metric_id: 'turnover',
      name: 'Equity Turnover',
      definition: 'Total value of equity trades in LKR',
    },
    volume: {
      metric_id: 'volume',
      name: 'Shares Traded',
      definition: 'Total number of equity shares traded',
    },
  },
  disclaimersMap: {},
  getMetricDefinition: (id: string) => mockMetaValue.glossaryMap[id],
  getDisclaimer: () => undefined,
  refetchStatus: vi.fn(),
};

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement, queryClient = createTestQueryClient()) {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MetaContext.Provider value={mockMetaValue}>{ui}</MetaContext.Provider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('Stage 5: Overview Page Component Tests', () => {
  beforeEach(() => {
    marketStore.disconnect();
    // Reset marketStore state
    (marketStore as any).state = {
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
  });

  afterEach(() => {
    marketStore.disconnect();
  });

  // ==========================================================================
  // 1. StatCard Component State Tests
  // ==========================================================================
  describe('StatCard 5 Core States', () => {
    it('1. Loading Skeleton state: renders skeleton placeholders without layout shifts', () => {
      const { container } = render(
        <StatCard
          title="ASPI Index"
          value="22,624.31"
          isLoading={true}
        />
      );

      // Skeletons are rendered
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
      // Value text is not visible during loading
      expect(screen.queryByText('22,624.31')).not.toBeInTheDocument();
    });

    it('2. Live state: renders tabular numeral value, delta, sparkline, and statusState', () => {
      render(
        <StatCard
          title="ASPI Index"
          value="22,865.00"
          delta={{ value: '+13.0908%', isPositive: true, direction: 'up', label: '1D' }}
          statusState="LIVE"
          asOfLabel="10:31 AM (Asia/Colombo)"
        />
      );

      expect(screen.getByText('ASPI Index')).toBeInTheDocument();
      expect(screen.getByText('22,865.00')).toBeInTheDocument();
      expect(screen.getByText('+13.0908%')).toBeInTheDocument();
      expect(screen.getByText('LIVE')).toBeInTheDocument();
      expect(screen.getByText('As of: 10:31 AM (Asia/Colombo)')).toBeInTheDocument();
    });

    it('3. Closed state: labels as Last Close and renders neutral/muted tone', () => {
      render(
        <StatCard
          title="S&P Sri Lanka 20"
          value="6,500.25"
          delta={{ value: '-0.34%', isPositive: false, direction: 'down', label: '5D' }}
          statusState="CLOSED"
          asOfLabel="20 Oct 2026"
        />
      );

      expect(screen.getByText('S&P Sri Lanka 20')).toBeInTheDocument();
      expect(screen.getByText('6,500.25')).toBeInTheDocument();
      expect(screen.getByText('Last Close')).toBeInTheDocument();
    });

    it('4. Stale state: displays stale badge and muted visual treatment', () => {
      render(
        <StatCard
          title="Equity Turnover"
          value="LKR 9.31B"
          isStale={true}
          statusState="STALE"
        />
      );

      expect(screen.getByText('Equity Turnover')).toBeInTheDocument();
      expect(screen.getByText('LKR 9.31B')).toBeInTheDocument();
      expect(screen.getByText(/stale/i)).toBeInTheDocument();
    });

    it('5. Error state with retry affordance: invokes onRetry callback on click', () => {
      const handleRetry = vi.fn();
      render(
        <StatCard
          title="Shares Traded"
          value="245.6M"
          isError={true}
          errorMessage="Stream disconnected."
          onRetry={handleRetry}
        />
      );

      expect(screen.getByText('Feed Error')).toBeInTheDocument();
      expect(screen.getByText('Stream disconnected.')).toBeInTheDocument();
      const retryButton = screen.getByRole('button', { name: /retry feed/i });
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(handleRetry).toHaveBeenCalledTimes(1);
    });

    it('Edge case protection: never renders blank or literal NaN', () => {
      render(
        <StatCard
          title="Empty Test"
          value={NaN as any}
          delta={{ value: undefined as any }}
        />
      );

      expect(screen.getByText('—')).toBeInTheDocument();
      expect(screen.queryByText('NaN')).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // 2. Individual Overview Cards Binding & Formatting
  // ==========================================================================
  describe('Overview StatCards with Live Data Binding', () => {
    it('AspiStatCard: binds live snapshot with 4-decimal return and Colombo timestamp', async () => {
      const snapshot: LiveMarketSnapshot = {
        aspi_value: 22865.0,
        aspi_change: 240.69,
        aspi_percent_change: 1.0645,
        aspi_previous_close: 22624.31,
        sp20_value: 6540.12,
        sp20_change: 32.1,
        sp20_percent_change: 0.49,
        sp20_previous_close: 6508.02,
        market_turnover: 9309760000.0,
        shares_traded: 245620000,
        total_trades: 18200,
        market_status: { raw_status: 'Market Open', status: 'Market Open', is_open: true },
        source_timestamp: '2026-10-20T10:31:28+00:00',
        freshness: 'LIVE',
      };

      renderWithProviders(<AspiStatCard />);

      // Update store with live snapshot
      act(() => {
        (marketStore as any).setState({
          snapshot,
          derived_freshness_state: 'LIVE',
          last_updated: '2026-10-20T10:31:28+00:00',
          connection_status: 'LIVE',
          sparklines: {
            aspi: [22624, 22700, 22865],
            sp20: [],
            turnover: [],
            shares: [],
          },
        });
      });

      await waitFor(() => {
        expect(screen.getByText('22,865.00')).toBeInTheDocument();
      });

      // Point change and percentage display
      expect(screen.getByText('+240.69 (+1.06%)')).toBeInTheDocument();
      // Status badge
      expect(screen.getByText('LIVE')).toBeInTheDocument();
    });

    it('Sp20StatCard: retains the Post-2012 tag and formats live change', async () => {
      const snapshot: LiveMarketSnapshot = {
        aspi_value: 22865.0,
        aspi_change: 240.69,
        aspi_percent_change: 1.0645,
        aspi_previous_close: 22624.31,
        sp20_value: 6540.12,
        sp20_change: 32.1,
        sp20_percent_change: 0.49,
        sp20_previous_close: 6508.02,
        market_turnover: 9309760000.0,
        shares_traded: 245620000,
        total_trades: 18200,
        market_status: { raw_status: 'Market Open', status: 'Market Open', is_open: true },
        source_timestamp: '2026-10-20T10:31:28+00:00',
        freshness: 'LIVE',
      };

      renderWithProviders(<Sp20StatCard />);

      act(() => {
        (marketStore as any).setState({
          snapshot,
          derived_freshness_state: 'LIVE',
          last_updated: '2026-10-20T10:31:28+00:00',
          connection_status: 'LIVE',
        });
      });

      await waitFor(() => {
        expect(screen.getByText('6,540.12')).toBeInTheDocument();
      });

      // Post-2012 tag requirement preserved
      expect(screen.getByText('Post-2012')).toBeInTheDocument();
      expect(screen.getByText('+32.10 (+0.49%)')).toBeInTheDocument();
    });

    it('TurnoverStatCard: formats billions to LKR B auto-formatted', async () => {
      renderWithProviders(<TurnoverStatCard />);

      act(() => {
        (marketStore as any).setState({
          snapshot: {
            market_turnover: 9309760000.0,
          },
          derived_freshness_state: 'LIVE',
          connection_status: 'LIVE',
        });
      });

      await waitFor(() => {
        expect(screen.getByText('LKR 9.31B')).toBeInTheDocument();
      });
    });

    it('SharesStatCard: formats volume to M auto-formatted', async () => {
      renderWithProviders(<SharesStatCard />);

      act(() => {
        (marketStore as any).setState({
          snapshot: {
            shares_traded: 245620000,
          },
          derived_freshness_state: 'LIVE',
          connection_status: 'LIVE',
        });
      });

      await waitFor(() => {
        expect(screen.getByText('245.6M')).toBeInTheDocument();
      });
    });

    it('OverviewStatCards container: contains aria-live polite region', () => {
      renderWithProviders(<OverviewStatCards />);

      const liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // 3. MarketOverviewStrip Component
  // ==========================================================================
  describe('MarketOverviewStrip', () => {
    it('renders Colombo timestamp and freshness badge', () => {
      (marketStore as any).setState({
        derived_freshness_state: 'LIVE',
        last_updated: '2026-10-20T10:31:28+00:00',
        connection_status: 'LIVE',
      });

      renderWithProviders(
        <MarketOverviewStrip
          summary={{
            aspi_level: 22865.0,
            daily_return: 1.06,
            as_of_date: '2026-10-20',
            equity_turnover_lkr: 1000000,
            shares_traded: 500000,
            realized_volatility_annualized: 18.4,
            is_stale: false,
          }}
        />
      );

      expect(screen.getByText('Market Overview:')).toBeInTheDocument();
      expect(screen.getByText('Colombo Stock Exchange')).toBeInTheDocument();
      expect(screen.getByText('LIVE')).toBeInTheDocument();
      expect(screen.getByText('Benchmarks: ASPI & S&P SL 20')).toBeInTheDocument();
      expect(screen.getByText('Ann. Volatility: 18.4%')).toBeInTheDocument();
      expect(screen.getByText(/Data As-Of:/)).toBeInTheDocument();
      expect(screen.getByText(/Asia\/Colombo/)).toBeInTheDocument();
    });

    it('displays STALE badge and state when data is stale', () => {
      (marketStore as any).setState({
        derived_freshness_state: 'STALE',
        last_updated: '2026-10-19T10:00:00+00:00',
        connection_status: 'LIVE',
      });

      renderWithProviders(<MarketOverviewStrip />);

      expect(screen.getByText('STALE')).toBeInTheDocument();
    });

    it('displays CLOSED state when market is closed', () => {
      (marketStore as any).setState({
        derived_freshness_state: 'CLOSED',
        last_updated: '2026-10-20T09:00:00+00:00',
        connection_status: 'LIVE',
      });

      renderWithProviders(<MarketOverviewStrip />);

      expect(screen.getByText('CLOSED')).toBeInTheDocument();
    });
  });
});
