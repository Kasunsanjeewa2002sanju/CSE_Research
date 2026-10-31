import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import {
  Button,
  IconButton,
  StatCard,
  Badge,
  Chip,
  SegmentedControl,
  Stepper,
  PageHeader,
  KeyValueList,
  EmptyState,
  ErrorState,
  ToastProvider,
  useToast,
  Table,
} from '@/components/ui';
import { ChartCard } from '@/components/charts';
import { Bell } from 'lucide-react';

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe('Design System UI Components', () => {
  describe('Button', () => {
    it('renders primary button using 10% cyan accent styling', () => {
      render(<Button variant="primary">Execute Analysis</Button>);
      const btn = screen.getByRole('button', { name: /execute analysis/i });
      expect(btn).toBeInTheDocument();
      expect(btn.className).toContain('bg-accent');
      expect(btn.className).toContain('text-accent-foreground');
    });

    it('renders loading state with disabled attribute and spinner', () => {
      render(<Button isLoading>Process Data</Button>);
      const btn = screen.getByRole('button', { name: /process data/i });
      expect(btn).toBeDisabled();
      expect(btn.querySelector('svg.animate-spin')).toBeInTheDocument();
    });

    it('handles click events properly', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click Me</Button>);
      fireEvent.click(screen.getByRole('button', { name: /click me/i }));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('IconButton', () => {
    it('renders with required aria-label for accessibility (Rule FR6)', () => {
      render(<IconButton aria-label="Notifications" icon={<Bell className="h-4 w-4" />} />);
      const btn = screen.getByRole('button', { name: /notifications/i });
      expect(btn).toBeInTheDocument();
      expect(btn).toHaveAttribute('aria-label', 'Notifications');
    });
  });

  describe('StatCard', () => {
    it('renders label, tabular numeral value, and positive delta', () => {
      render(
        <StatCard
          title="Current ASPI Index"
          value="11,842.50"
          delta={{ value: 142.3, percentage: 1.22, isPositive: true }}
          asOfLabel="2024-09-30"
        />
      );
      expect(screen.getByText('Current ASPI Index')).toBeInTheDocument();
      expect(screen.getByText('11,842.50')).toBeInTheDocument();
      expect(screen.getByText('+1.22%')).toBeInTheDocument();
      expect(screen.getByText('As of: 2024-09-30')).toBeInTheDocument();
    });

    it('renders glossary definition hover tooltip icon when provided', () => {
      render(
        <StatCard
          title="CAAR"
          value="+3.85%"
          glossaryDefinition="Cumulative Average Abnormal Return"
        />
      );
      expect(screen.getByLabelText(/definition for caar/i)).toBeInTheDocument();
    });
  });

  describe('Badge and Chip', () => {
    it('renders categorical impact and evidence badges with correct tokens', () => {
      const { rerender } = render(<Badge variant="impact-high">Critical Event</Badge>);
      expect(screen.getByText('Critical Event')).toHaveClass('text-data-down');

      rerender(<Badge variant="evidence-strong">Robust Evidence</Badge>);
      expect(screen.getByText('Robust Evidence')).toHaveClass('text-data-up');
    });

    it('renders interactive chip with remove button', () => {
      const handleRemove = vi.fn();
      render(<Chip label="Presidential Election" active onRemove={handleRemove} />);
      expect(screen.getByText('Presidential Election')).toBeInTheDocument();
      const removeBtn = screen.getByRole('button', { name: /remove filter/i });
      fireEvent.click(removeBtn);
      expect(handleRemove).toHaveBeenCalledTimes(1);
    });
  });

  describe('Stepper (Six Election Stages)', () => {
    it('renders all 6 constitutional election stages with active step highlighted', () => {
      render(<Stepper currentStage={3} />);
      expect(screen.getByText('Proclamation')).toBeInTheDocument();
      expect(screen.getByText('Nominations')).toBeInTheDocument();
      expect(screen.getByText('Campaign Window')).toBeInTheDocument();
      expect(screen.getByText('Polling Day')).toBeInTheDocument();
      expect(screen.getByText('Results Declaration')).toBeInTheDocument();
      expect(screen.getByText('Regime Settlement')).toBeInTheDocument();

      // Step 3 should be marked as active step
      const step3 = screen.getByText('Campaign Window').closest('li');
      expect(step3).toHaveAttribute('aria-current', 'step');
    });
  });

  describe('SegmentedControl', () => {
    it('allows switching horizon options with active pill indication', () => {
      const handleChange = vi.fn();
      render(
        <SegmentedControl
          value="1M"
          onChange={handleChange}
          options={[
            { value: '1W', label: '1W' },
            { value: '1M', label: '1M' },
            { value: '3M', label: '3M' },
          ]}
        />
      );

      const opt3M = screen.getByRole('radio', { name: '3M' });
      fireEvent.click(opt3M);
      expect(handleChange).toHaveBeenCalledWith('3M');
    });
  });

  describe('PageHeader and Breadcrumbs', () => {
    it('renders title, description, and breadcrumb path', () => {
      renderWithRouter(
        <PageHeader
          title="Political Event Study"
          description="Econometric CAAR analysis over Sri Lankan elections."
          breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Event Study' }]}
        />
      );

      expect(
        screen.getByRole('heading', { level: 1, name: /political event study/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/econometric caar analysis/i)).toBeInTheDocument();
      expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toBeInTheDocument();
    });
  });

  describe('KeyValueList', () => {
    it('renders key-value pairs with tabular numerals', () => {
      render(
        <KeyValueList
          items={[
            { key: 'Estimation Window', value: '250 Days' },
            { key: 'Event Window', value: '[-20, +20]' },
          ]}
        />
      );

      expect(screen.getByText('Estimation Window')).toBeInTheDocument();
      expect(screen.getByText('250 Days')).toBeInTheDocument();
      expect(screen.getByText('[-20, +20]')).toBeInTheDocument();
    });
  });

  describe('EmptyState and ErrorState', () => {
    it('renders EmptyState with FR9 gap documentation message', () => {
      render(
        <EmptyState
          title="No Data Available"
          message="Module scheduled for Stage F2."
          gapId="GAP-001"
        />
      );

      expect(screen.getByText('No Data Available')).toBeInTheDocument();
      expect(screen.getByText(/module scheduled for stage f2/i)).toBeInTheDocument();
      expect(screen.getByText(/registered gap: gap-001/i)).toBeInTheDocument();
    });

    it('renders ErrorState with retry button', () => {
      const handleRetry = vi.fn();
      render(<ErrorState message="Compute daemon offline" onRetry={handleRetry} />);

      expect(screen.getByText('Compute daemon offline')).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryBtn);
      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Table Component', () => {
    it('renders tabular data, supports column sorting and CSV export', () => {
      const data = [
        { id: 'E1', name: 'Event A', score: 95 },
        { id: 'E2', name: 'Event B', score: 80 },
      ];
      const cols = [
        { key: 'id', header: 'ID', sortable: true },
        { key: 'name', header: 'Name', sortable: true },
        { key: 'score', header: 'Score', sortable: true },
      ];

      render(<Table data={data} columns={cols} keyField="id" />);

      expect(screen.getByText('Event A')).toBeInTheDocument();
      expect(screen.getByText('Event B')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();

      // Click header to sort
      const nameHeader = screen.getByRole('button', { name: 'Name' });
      fireEvent.click(nameHeader);
      expect(nameHeader.closest('th')).toHaveAttribute('aria-sort', 'ascending');
    });
  });

  describe('ChartCard Wrapper & Accessible Fallback', () => {
    it('renders chart title, subtitle, and switches to accessible data table fallback', () => {
      render(
        <ChartCard
          title="CAAR Trajectory"
          subtitle="41-day event window"
          dataTableData={[
            { Day: '-1d', Return: '0.8%' },
            { Day: '0d', Return: '1.9%' },
          ]}
          dataTableColumns={[
            { key: 'Day', header: 'Event Day', sortable: true },
            { key: 'Return', header: 'Abnormal Return', sortable: true },
          ]}
        >
          <div data-testid="chart-graphic">Mock EChart Canvas</div>
        </ChartCard>
      );

      expect(screen.getByText('CAAR Trajectory')).toBeInTheDocument();
      expect(screen.getByText('41-day event window')).toBeInTheDocument();
      expect(screen.getByTestId('chart-graphic')).toBeInTheDocument();

      // Switch to accessible data table
      const toggleBtn = screen.getByRole('button', {
        name: /switch to accessible data table view/i,
      });
      fireEvent.click(toggleBtn);

      expect(screen.getByText('0.8%')).toBeInTheDocument();
      expect(screen.getByText('1.9%')).toBeInTheDocument();
    });
  });

  describe('Toast Notifications', () => {
    function TestConsumer() {
      const { toast } = useToast();
      return (
        <button
          onClick={() =>
            toast({
              title: 'Action Succeeded',
              description: 'Changes persisted to backend.',
              variant: 'success',
            })
          }
        >
          Trigger Toast
        </button>
      );
    }

    it('triggers and renders a notification message', () => {
      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /trigger toast/i }));
      expect(screen.getByText('Action Succeeded')).toBeInTheDocument();
      expect(screen.getByText('Changes persisted to backend.')).toBeInTheDocument();
    });
  });
});
