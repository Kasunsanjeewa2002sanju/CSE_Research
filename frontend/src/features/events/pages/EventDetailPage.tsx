import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { useEventDetailQuery } from '../hooks/useEventsData';
import { useMarketSeriesQuery } from '@/features/data-explorer/hooks/useDataExplorerData';
import { EventDetailContent } from '../components/EventDetailContent';

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = id || '';

  const { data: event, isLoading, error } = useEventDetailQuery(eventId);
  const { data: marketData } = useMarketSeriesQuery('All');
  const fullSeries = marketData?.series ?? marketData?.points ?? [];

  if (isLoading) { 
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48 rounded-lg" />
        <Skeleton className="h-28 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="bg-bg-surface space-y-4 rounded-xl border border-border p-8 text-center">
        <AlertCircle className="text-warning mx-auto h-10 w-10" />
        <h3 className="text-text text-base font-bold">Event Not Found</h3>
        <p className="text-muted mx-auto max-w-md text-xs">
          The requested political event identifier &quot;{eventId}&quot; could not be resolved in
          the 30-year empirical catalog.
        </p>
        <Link to="/events">
          <Button variant="outline" size="sm" className="gap-1.5">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Events Catalog
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/events">
          <Button variant="ghost" size="sm" className="text-muted hover:text-text gap-1.5 text-xs">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Events Catalog
          </Button>
        </Link>
      </div>

      <PageHeader
        title={event.name}
        description={`Empirical event documentation for the ${event.name}, mapped to Colombo Stock Exchange trading sessions.`}
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Political Events', to: '/events' },
          { label: event.name },
        ]}
      />

      <div className="max-w-4xl">
        <EventDetailContent event={event} fullSeries={fullSeries} isDrawer={false} />
      </div>
    </div>
  );
}
