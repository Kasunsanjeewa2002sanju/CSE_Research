import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/api/query-client';
import { ToastProvider } from '@/components/ui/Toast';
import { MetaProvider } from '@/context/MetaContext';
import { ErrorBoundary } from './ErrorBoundary';

export interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <MetaProvider>{children}</MetaProvider>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
