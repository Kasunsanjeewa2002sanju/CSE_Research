import { Component, ErrorInfo, ReactNode } from 'react';
import { ContractValidationError, BackendOfflineError } from '@/api/client';
import { ContractError } from '@/components/feedback/ContractError';
import { BackendUnavailable } from '@/components/feedback/BackendUnavailable';
import { Button } from '@/components/ui/Button';
import { AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[Uncaught Application Error]', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError && this.state.error) {
      if (this.state.error instanceof ContractValidationError) {
        return (
          <div className="p-6">
            <ContractError
              endpoint={this.state.error.endpoint}
              error={this.state.error}
              onRetry={this.handleReset}
            />
          </div>
        );
      }

      if (this.state.error instanceof BackendOfflineError) {
        return (
          <div className="p-6">
            <BackendUnavailable endpoint={this.state.error.endpoint} onRetry={this.handleReset} />
          </div>
        );
      }

      return (
        <div className="border-destructive/20 bg-destructive/5 mx-auto my-12 max-w-md space-y-4 rounded-lg border p-8 text-center">
          <AlertCircle className="text-destructive mx-auto h-10 w-10" />
          <h3 className="font-heading text-lg font-semibold">Application Render Error</h3>
          <p className="text-muted-foreground font-mono text-xs">{this.state.error.message}</p>
          <Button variant="outline" size="sm" onClick={this.handleReset}>
            Reload Component
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
