import { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Drawer } from '@/components/ui/Drawer';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Clock, Table as TableIcon, Layers, BarChart2, X } from 'lucide-react';
import { useEventsListQuery, useEventsCoverageQuery } from '../hooks/useEventsData';
import { useMarketSeriesQuery } from '@/features/data-explorer/hooks/useDataExplorerData';
import { EventsTimelineView } from '../components/EventsTimelineView';
import { EventsTableView } from '../components/EventsTableView';
import { EventsCoveragePanel } from '../components/EventsCoveragePanel';
import { EventDetailContent } from '../components/EventDetailContent';
import { EventCompareModal } from '../components/EventCompareModal';
import { Skeleton } from '@/components/ui/Skeleton';
import type { PoliticalEvent } from '@/api/types';
 
export default function EventsPage() {
  const [activeTab, setActiveTab] = useState<'timeline' | 'table' | 'coverage'>('timeline');
  const [selectedDrawerEvent, setSelectedDrawerEvent] = useState<PoliticalEvent | null>(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState<string[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  // Queries
  const { data: eventsData, isLoading: isEventsLoading } = useEventsListQuery();
  const { data: coverageData, isLoading: isCoverageLoading } = useEventsCoverageQuery();
  const { data: marketData } = useMarketSeriesQuery('All');

  const events = eventsData?.events ?? [];
  const fullSeries = marketData?.series ?? marketData?.points ?? [];

  const handleToggleCompare = (eventId: string) => {
    setSelectedCompareIds((prev) => {
      if (prev.includes(eventId)) {
        return prev.filter((id) => id !== eventId);
      }
      if (prev.length >= 3) {
        return prev;
      }
      return [...prev, eventId];
    });
  };

  const selectedCompareEvents = events.filter((e) => selectedCompareIds.includes(e.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Sri Lankan Political Events Catalog"
        description="Comprehensive 30-year empirical catalog of 24 national elections across 146 stages, mapped to Colombo Stock Exchange trading sessions."
        breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Political Events' }]}
      />

      {/* Primary Tab Navigation */}
      <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as typeof activeTab)}>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
          <TabsList className="bg-bg-muted rounded-xl p-1">
            <TabsTrigger value="timeline" className="gap-1.5 px-4 py-2 text-xs font-semibold">
              <Clock className="h-3.5 w-3.5" />
              Chronological Timeline
            </TabsTrigger>
            <TabsTrigger value="table" className="gap-1.5 px-4 py-2 text-xs font-semibold">
              <TableIcon className="h-3.5 w-3.5" />
              Catalog Table & Filters
            </TabsTrigger>
            <TabsTrigger value="coverage" className="gap-1.5 px-4 py-2 text-xs font-semibold">
              <Layers className="h-3.5 w-3.5" />
              Empirical Coverage Panel
            </TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            <span className="text-muted font-mono text-xs">
              {events.length} Events • {coverageData?.total_stages ?? 146} Stages
            </span>
          </div>
        </div>

        {/* Tab 1: Timeline */}
        <TabsContent value="timeline" className="mt-4">
          {isEventsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-12 w-full rounded-xl" />
              <Skeleton className="h-64 w-full rounded-xl" />
            </div>
          ) : (
            <EventsTimelineView
              events={events}
              onSelectEvent={(e) => setSelectedDrawerEvent(e)}
              selectedEventId={selectedDrawerEvent?.id}
            />
          )}
        </TabsContent>

        {/* Tab 2: Table */}
        <TabsContent value="table" className="mt-4">
          {isEventsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-72 w-full rounded-xl" />
            </div>
          ) : (
            <EventsTableView
              events={events}
              onSelectEvent={(e) => setSelectedDrawerEvent(e)}
              selectedCompareIds={selectedCompareIds}
              onToggleCompare={handleToggleCompare}
            />
          )}
        </TabsContent>

        {/* Tab 3: Coverage */}
        <TabsContent value="coverage" className="mt-4">
          <EventsCoveragePanel coverage={coverageData} isLoading={isCoverageLoading} />
        </TabsContent>
      </Tabs>

      {/* Floating Compare Action Bar (Rule FR11) */}
      {selectedCompareIds.length > 0 && (
        <div className="bg-bg-surface border-primary/40 animate-slide-up fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 transform items-center gap-4 rounded-2xl border p-3 px-5 shadow-xl">
          <div className="text-text flex items-center gap-2 text-xs font-semibold">
            <BarChart2 className="h-4 w-4 text-accent" />
            <span>{selectedCompareIds.length}/3 Events Selected for Comparison</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCompareModalOpen(true)}
              className="h-8 px-4 text-xs"
            >
              Compare Trajectories (FR11)
            </Button>
            <button
              onClick={() => setSelectedCompareIds([])}
              className="text-muted hover:text-text p-1"
              aria-label="Clear selection"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Event Detail Drawer */}
      <Drawer
        open={Boolean(selectedDrawerEvent)}
        onClose={() => setSelectedDrawerEvent(null)}
        title={selectedDrawerEvent?.name || 'Event Inspection'}
        className="w-full sm:max-w-xl"
      >
        {selectedDrawerEvent && (
          <EventDetailContent event={selectedDrawerEvent} fullSeries={fullSeries} isDrawer={true} />
        )}
      </Drawer>

      {/* Event Compare Modal */}
      <EventCompareModal
        events={selectedCompareEvents}
        fullSeries={fullSeries}
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        onRemoveEvent={(id) => handleToggleCompare(id)}
      />
    </div>
  );
}
