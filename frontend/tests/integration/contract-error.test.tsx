import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ContractError } from '@/components/feedback/ContractError';
import { BackendUnavailable } from '@/components/feedback/BackendUnavailable';
import { z } from 'zod';

describe('Error State Components (Rules FR3 & FR4)', () => {
  it('renders ContractError component with endpoint and violation details', () => {
    const dummySchema = z.object({ value: z.number() });
    const parseResult = dummySchema.safeParse({ value: 'invalid_string' });
    if (parseResult.success) throw new Error('Expected failure');

    const error = Object.assign(new Error('Validation failed'), {
      zodError: parseResult.error,
      rawPayload: { value: 'invalid_string' },
    });

    render(<ContractError endpoint="/overview/summary" error={error} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/Rule FR4: Contract Error/i)).toBeInTheDocument();
    expect(screen.getByText('/overview/summary')).toBeInTheDocument();
  });

  it('renders BackendUnavailable with clear retry message and no mock data', () => {
    render(<BackendUnavailable endpoint="/aspi/history" />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/Rule FR3: No Mock Fallback/i)).toBeInTheDocument();
    expect(screen.getByText(/Backend Service Offline/i)).toBeInTheDocument();
  });
});
