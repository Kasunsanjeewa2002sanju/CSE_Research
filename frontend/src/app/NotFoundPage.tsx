import { Link, useNavigate } from 'react-router-dom';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Compass, Home, ArrowLeft, Search } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <Breadcrumbs items={[{ label: 'Overview', to: '/' }, { label: '404 Not Found' }]} />

      <PageHeader
        title="404 — Page Not Found"
        description="The requested route does not match any registered econometric research module or view."
      />

      <Card className="bg-card/60 mx-auto my-8 max-w-xl border-border p-8 text-center backdrop-blur-sm">
        <CardContent className="space-y-6 pt-4">
          <div className="bg-surface-muted text-primary mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-border">
            <Compass className="h-8 w-8 animate-pulse text-accent" />
          </div>

          <div className="space-y-2">
            <h3 className="text-foreground font-heading text-xl font-bold">
              Unmapped Research Route
            </h3>
            <p className="text-muted-foreground mx-auto max-w-md text-sm leading-relaxed">
              Please verify the URL or select a research module from the top navigation bar. All
              data views adhere to strict zero-lookahead walk-forward specifications.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button
              variant="secondary"
              onClick={() => navigate(-1)}
              icon={<ArrowLeft className="h-4 w-4" />}
            >
              Go Back
            </Button>
            <Button variant="primary" asChild icon={<Home className="h-4 w-4" />}>
              <Link to="/">Overview Dashboard</Link>
            </Button>
            <Button variant="outline" asChild icon={<Search className="h-4 w-4" />}>
              <Link to="/events">Political Events</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
