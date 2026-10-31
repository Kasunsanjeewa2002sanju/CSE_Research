import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { ContractError } from '@/components/ui/ContractError';
import { ContractValidationError } from '@/api/client';

export function ErrorPage() {
  const error = useRouteError();

  let errorMessage = 'An unexpected runtime error occurred within the dashboard.';
  let errorTitle = 'Dashboard Render Exception';

  if (isRouteErrorResponse(error)) {
    errorTitle = `${error.status} — ${error.statusText}`;
    errorMessage = error.data?.message || error.statusText;
  } else if (error instanceof ContractValidationError) {
    return (
      <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
        <ContractError
          endpoint={error.endpoint}
          error={error}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  } else if (error instanceof Error) {
    errorMessage = error.message;
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <Breadcrumbs items={[{ label: 'Overview', to: '/' }, { label: 'Application Error' }]} />

      <PageHeader
        title={errorTitle}
        description="The dashboard encountered an unhandled exception while preparing this view."
      />

      <Card className="border-destructive/20 bg-destructive/5 mx-auto my-8 max-w-xl p-8 text-center backdrop-blur-sm">
        <CardContent className="space-y-6 pt-4">
          <div className="bg-destructive/10 border-destructive/20 text-destructive mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border">
            <AlertCircle className="h-8 w-8" />
          </div>

          <div className="space-y-2">
            <h3 className="text-foreground font-heading text-lg font-bold">
              Module Execution Halted
            </h3>
            <p className="text-muted-foreground bg-surface-muted overflow-x-auto rounded border border-border p-3 text-left font-mono text-xs">
              {errorMessage}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
              icon={<RefreshCw className="h-4 w-4" />}
            >
              Reload Page
            </Button>
            <Button variant="primary" asChild icon={<Home className="h-4 w-4" />}>
              <Link to="/">Return to Overview</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
