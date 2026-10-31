import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Badge } from '@/components/ui/Badge';
import { Layers, Database, ArrowRight } from 'lucide-react';
import { PageContainer } from './PageContainer';
import type { BreadcrumbItem } from '@/components/ui/Breadcrumbs';

interface RouteSkeletonProps {
  title: string;
  description: string;
  breadcrumbs: BreadcrumbItem[];
  stageScheduled: string;
  stageName: string;
  badgeLabel?: string;
  dataPointsDescription?: string;
}

export function RouteSkeleton({
  title,
  description,
  breadcrumbs,
  stageScheduled,
  stageName,
  badgeLabel = 'Stage F1 App Shell',
  dataPointsDescription,
}: RouteSkeletonProps) {
  return (
    <PageContainer
      title={title}
      description={description}
      breadcrumbs={breadcrumbs}
      badge={<Badge variant="outline">{badgeLabel}</Badge>}
    >
      <div className="space-y-6">
        {/* Status card showing clean contract schedule */}
        <Card className="from-card via-card to-blue-sky/30 border-border bg-gradient-to-r">
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="bg-accent/15 rounded-md p-1.5 text-accent-hover">
                  <Database className="h-4 w-4" />
                </span>
                <CardTitle className="text-base font-semibold">
                  Data Pipeline & Contract Scheduled
                </CardTitle>
              </div>
              <Badge variant="secondary" className="font-mono text-xs">
                {stageScheduled}: {stageName}
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Adhering to Rule FR1 (No Hardcoded Domain Data). Real endpoints, validation schemas,
              and live market feeds are wired in {stageScheduled}.
            </CardDescription>
          </CardHeader>
          {dataPointsDescription && (
            <CardContent className="text-muted-foreground flex items-center gap-2 pt-0 font-mono text-xs">
              <ArrowRight className="h-3 w-3 shrink-0 text-accent" />
              <span>Target contracts: {dataPointsDescription}</span>
            </CardContent>
          )}
        </Card>

        {/* Skeleton StatCard grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-4 w-4 rounded-full" />
              </div>
              <Skeleton className="h-8 w-28" />
              <div className="flex items-center gap-2 pt-1">
                <Skeleton className="h-3 w-12" />
                <Skeleton className="h-3 w-24" />
              </div>
            </Card>
          ))}
        </div>

        {/* Skeleton Chart / Data Area */}
        <Card className="space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-3 w-72" />
            </div>
            <div className="flex items-center gap-2">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-8 rounded-md" />
            </div>
          </div>
          <div className="bg-surface-muted/60 flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-border p-6 text-center">
            <EmptyState
              icon={Layers}
              title="Interface Shell Initialized"
              description={`This view's data queries and visualizations will be connected in ${stageScheduled} (${stageName}).`}
              gapMessage="Scheduled per architectural roadmap"
            />
          </div>
        </Card>
      </div>
    </PageContainer>
  );
}
